import itertools
import secrets

import pytest
from langchain_core.language_models.fake_chat_models import GenericFakeChatModel
from langchain_core.messages import AIMessage

from app import draft
from app.admin_agent import AdminAgent
from app.admin_api import create_app as create_admin_app
from app.admin_client import AdminClient
from app.bookings import allocate_for, free_by_zone
from app.load_test import running_server
from app.mcp_client import ReservationRecorder
from app.mcp_server import create_app as create_mcp_app
from app.seed_db import seed
from app.workflow import Workflow

REQUEST = {
    "first_name": "Likhith",
    "last_name": "Edupuganti",
    "car_number": "TS09AB1234",
    "start": "2099-01-01 10:00",
    "end": "2099-01-01 12:00",
}

EXPECTED_PREFIX = "Likhith Edupuganti | TS09AB1234 | 2099-01-01 10:00 to 2099-01-01 12:00 | "


class ScriptedModel(GenericFakeChatModel):
    def bind_tools(self, tools, **kwargs):
        return self


def scripted_note_model():
    note = AIMessage(
        content="",
        tool_calls=[
            {"name": "send_to_administrator", "args": {"note": "Integration test booking."}, "id": "c1"}
        ],
    )
    return ScriptedModel(messages=itertools.cycle([note, AIMessage(content="DONE")]))


def chat_fn(session, message):
    if message == "book":
        draft.set_ready(session, dict(REQUEST))
        return "Submitted."
    return f"echo {message}"


@pytest.fixture(autouse=True)
def clean(monkeypatch):
    for name in ("_drafts", "_turns", "_ready", "_last_request"):
        monkeypatch.setattr(draft, name, {})
    monkeypatch.setattr(draft, "_sent", set())


class Stack:
    def __init__(self, client, recorder, agent, workflow, reservations, parking_db):
        self.client = client
        self.recorder = recorder
        self.agent = agent
        self.workflow = workflow
        self.reservations = reservations
        self.parking_db = parking_db

    def lines(self):
        if not self.reservations.exists():
            return []
        return self.reservations.read_text(encoding="utf-8").splitlines()

    def free_spaces(self, start, end):
        rows = free_by_zone(start, end, db_path=self.parking_db)
        return sum(row["free_spaces"] for row in rows)


@pytest.fixture
def stack(tmp_path):
    """The real admin service and the real MCP server. Only the language model is scripted."""
    admin_key = secrets.token_urlsafe(8)
    mcp_key = secrets.token_urlsafe(8)
    reservations = tmp_path / "reservations.txt"
    parking_db = tmp_path / "parking.db"
    seed(parking_db)

    admin_app = create_admin_app(db_path=tmp_path / "admin.db", api_key=admin_key)
    mcp_app = create_mcp_app(path=reservations, api_key=mcp_key)

    with running_server(admin_app) as admin_url, running_server(mcp_app) as mcp_url:
        client = AdminClient(base_url=admin_url, api_key=admin_key)
        recorder = ReservationRecorder(url=f"{mcp_url}/mcp", api_key=mcp_key)
        agent = AdminAgent(
            client=client,
            llm=scripted_note_model(),
            recorder=recorder,
            allocator=lambda record: allocate_for(record, parking_db),
        )
        workflow = Workflow(chat_fn, agent, retry_delay=0)
        yield Stack(client, recorder, agent, workflow, reservations, parking_db)
        client.close()


def request_id_from(reply):
    return next(word.strip(".") for word in reply.split() if word.startswith("RES-"))


def test_approved_booking_flows_from_chat_to_the_reservations_file(stack):
    reply = stack.workflow.send("s", "book")
    request_id = request_id_from(reply)
    assert stack.client.get_request(request_id)["status"] == "PENDING"
    assert "Integration test booking." in stack.client.get_request(request_id)["note"]

    assert stack.workflow.poll() == []
    assert stack.lines() == []

    stack.client.decide(request_id, "APPROVED", "see you then")
    (session, text), = stack.workflow.poll()

    assert session == "s"
    assert "approved" in text and "see you then" in text and "now saved" in text
    lines = stack.lines()
    assert len(lines) == 1
    assert lines[0].startswith(EXPECTED_PREFIX)
    assert len(lines[0].split(" | ")) == 4


def test_refused_booking_never_reaches_the_file(stack):
    request_id = request_id_from(stack.workflow.send("s", "book"))
    stack.client.decide(request_id, "REFUSED", "zone full")

    (_, text), = stack.workflow.poll()

    assert "refused" in text
    assert stack.lines() == []


def test_a_booking_is_saved_once_even_if_it_is_settled_twice(stack):
    request_id = request_id_from(stack.workflow.send("s", "book"))
    stack.client.decide(request_id, "APPROVED")
    stack.workflow.poll()

    _, recording = stack.agent.settle(request_id)

    assert recording == "ALREADY_RECORDED"
    assert len(stack.lines()) == 1


def test_a_down_mcp_server_is_reported_and_reconcile_recovers_the_booking(stack):
    working_recorder = stack.agent.recorder
    stack.agent.recorder = ReservationRecorder(
        url="http://127.0.0.1:1/mcp", api_key="x", timeout=3
    )
    request_id = request_id_from(stack.workflow.send("s", "book"))
    stack.client.decide(request_id, "APPROVED")

    (_, text), = stack.workflow.poll()

    assert "could not be saved" in text
    assert stack.lines() == []

    stack.agent.recorder = working_recorder
    assert stack.workflow.reconcile() == 1
    assert len(stack.lines()) == 1
    assert stack.workflow.reconcile() == 0


def test_approvals_decided_while_no_conversation_runs_are_saved_on_startup(stack):
    record = stack.client.submit_request(**REQUEST, note="offline approval")
    stack.client.decide(record["id"], "APPROVED")

    fresh = Workflow(chat_fn, stack.agent, retry_delay=0)

    assert fresh.reconcile() == 1
    assert len(stack.lines()) == 1


def test_an_approved_booking_takes_a_space_for_its_period_only(stack):
    period = (REQUEST["start"], REQUEST["end"])
    other = ("2099-02-01 10:00", "2099-02-01 12:00")
    before, before_other = stack.free_spaces(*period), stack.free_spaces(*other)

    request_id = request_id_from(stack.workflow.send("s", "book"))
    stack.client.decide(request_id, "APPROVED")
    stack.workflow.poll()

    assert stack.free_spaces(*period) == before - 1
    assert stack.free_spaces(*other) == before_other


def test_a_refused_booking_takes_no_space(stack):
    period = (REQUEST["start"], REQUEST["end"])
    before = stack.free_spaces(*period)

    request_id = request_id_from(stack.workflow.send("s", "book"))
    stack.client.decide(request_id, "REFUSED")
    stack.workflow.poll()

    assert stack.free_spaces(*period) == before