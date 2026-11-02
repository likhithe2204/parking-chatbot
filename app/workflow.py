import logging
import threading
import time
from typing import Callable, TypedDict

from langgraph.checkpoint.memory import InMemorySaver
from langgraph.graph import END, START, StateGraph
from langgraph.types import Command, interrupt

from app import draft
from app.admin_client import AdminServiceError
from app.mcp_client import RecorderError
from app.messages import status_message

logger = logging.getLogger(__name__)

NOT_SENT = (
    "Update: I could not reach the administrator, so your request was NOT sent. "
    "Please try again in a moment."
)
SENT = (
    "Your request id is {request_id}. It is NOT confirmed yet. You can ask for its "
    "status at any time, and I will tell you here as soon as the administrator decides."
)


class State(TypedDict, total=False):
    session: str
    user_message: str
    reply: str
    request: dict | None
    request_id: str
    decision: dict
    recording: str
    notification: str


def _after_chatbot(state: State) -> str:
    return "escalate" if state.get("request") else "reply"


def _after_escalate(state: State) -> str:
    return "await_approval" if state.get("request_id") else "reply"


def _after_approval(state: State) -> str:
    return "record" if state["decision"]["status"] == "APPROVED" else "notify"


class Workflow:
    """The whole pipeline as one LangGraph graph.

    chatbot -> escalate -> await_approval (human decides) -> record -> notify
    """

    def __init__(self, chat_fn: Callable[[str, str], str], admin, record_attempts: int = 3,
                 retry_delay: float = 1.0):
        self.chat_fn = chat_fn
        self.admin = admin
        self.record_attempts = record_attempts
        self.retry_delay = retry_delay
        self._mutex = threading.Lock()
        self._turn = 0
        self._waiting: dict[str, tuple[str, str]] = {}
        self.graph = self._build()

    # ---- nodes -----------------------------------------------------------

    def _chatbot(self, state: State) -> dict:
        session = state["session"]
        reply = self.chat_fn(session, state["user_message"])
        return {"reply": reply, "request": draft.take_ready(session)}

    def _escalate(self, state: State) -> dict:
        request = state["request"]
        try:
            escalation = self.admin.escalate(
                request["first_name"],
                request["last_name"],
                request["car_number"],
                request["start"],
                request["end"],
            )
        except AdminServiceError as exc:
            logger.warning("Could not reach the administrator: %s", exc)
            return {"reply": f"{state['reply']}\n\n{NOT_SENT}", "request_id": ""}

        draft.clear_draft(state["session"])
        draft.remember_request(state["session"], escalation.request_id)
        text = SENT.format(request_id=escalation.request_id)
        return {"reply": f"{state['reply']}\n\n{text}", "request_id": escalation.request_id}

    def _await_approval(self, state: State) -> dict:
        decision = interrupt({"request_id": state["request_id"], "waiting_for": "administrator"})
        return {"decision": decision}

    def _record(self, state: State) -> dict:
        recording = "RECORD_FAILED"
        for attempt in range(self.record_attempts):
            try:
                _, recording = self.admin.settle(state["request_id"])
            except (AdminServiceError, RecorderError) as exc:
                logger.warning("Saving attempt %s failed: %s", attempt + 1, exc)
                recording = "RECORD_FAILED"
            if recording != "RECORD_FAILED":
                break
            if attempt + 1 < self.record_attempts:
                time.sleep(self.retry_delay)
        return {"recording": recording}

    def _notify(self, state: State) -> dict:
        text = status_message(state["decision"], state.get("recording", "NOT_APPROVED"))
        return {"notification": text}

    # ---- graph -----------------------------------------------------------

    def _build(self):
        graph = StateGraph(State)
        graph.add_node("chatbot", self._chatbot)
        graph.add_node("escalate", self._escalate)
        graph.add_node("await_approval", self._await_approval)
        graph.add_node("record", self._record)
        graph.add_node("notify", self._notify)

        graph.add_edge(START, "chatbot")
        graph.add_conditional_edges("chatbot", _after_chatbot, {"escalate": "escalate", "reply": END})
        graph.add_conditional_edges(
            "escalate", _after_escalate, {"await_approval": "await_approval", "reply": END}
        )
        graph.add_conditional_edges(
            "await_approval", _after_approval, {"record": "record", "notify": "notify"}
        )
        graph.add_edge("record", "notify")
        graph.add_edge("notify", END)
        return graph.compile(checkpointer=InMemorySaver())

    # ---- running it ------------------------------------------------------

    @property
    def waiting(self) -> int:
        with self._mutex:
            return len(self._waiting)

    def send(self, session: str, message: str) -> str:
        """Run one customer message through the graph and return the reply."""
        with self._mutex:
            self._turn += 1
            thread = f"{session}#{self._turn}"
        config = {"configurable": {"thread_id": thread}}

        self.graph.invoke({"session": session, "user_message": message}, config)
        snapshot = self.graph.get_state(config)
        if snapshot.next == ("await_approval",):
            with self._mutex:
                self._waiting[thread] = (session, snapshot.values["request_id"])
        return snapshot.values.get("reply", "")

    def poll(self) -> list[tuple[str, str]]:
        """Resume every waiting reservation whose administrator decision has arrived.
        Returns (session, message for the customer) pairs."""
        with self._mutex:
            waiting = list(self._waiting.items())

        notifications = []
        for thread, (session, request_id) in waiting:
            try:
                record = self.admin.get_decision(request_id)
                if record["status"] == "PENDING":
                    continue
                config = {"configurable": {"thread_id": thread}}
                self.graph.invoke(Command(resume=record), config)
                notification = self.graph.get_state(config).values["notification"]
            except Exception as exc:  # keep waiting and try again on the next poll
                logger.warning("Could not settle request %s: %s", request_id, exc)
                continue
            with self._mutex:
                self._waiting.pop(thread, None)
            notifications.append((session, notification))
        return notifications


    def reconcile(self) -> int:
        """Save approved bookings that were decided while no conversation was running.
        Safe to repeat: a space is taken and a line written only once per booking."""
        saved = 0
        for record in self.admin.client.list_requests("APPROVED"):
            try:
                _, recording = self.admin.settle(record["id"])
            except (AdminServiceError, RecorderError) as exc:
                logger.warning("Could not settle %s: %s", record["id"], exc)
                continue
            if recording == "RECORDED":
                saved += 1
        return saved


def create_workflow() -> Workflow:
    from app.agent import build_agent, chat
    from app.tools import get_admin_agent

    agent = build_agent()
    return Workflow(
        lambda session, message: chat(agent, message, thread_id=session),
        get_admin_agent(),
    )