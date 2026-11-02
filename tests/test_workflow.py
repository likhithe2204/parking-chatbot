from types import SimpleNamespace

import pytest

from app import draft
from app.admin_client import AdminServiceError
from app.mcp_client import RecorderError
from app.workflow import NOT_SENT, Workflow

REQUEST = {
    "first_name": "Likhith",
    "last_name": "Edupuganti",
    "car_number": "TS09AB1234",
    "start": "2099-01-01 10:00",
    "end": "2099-01-01 12:00",
}


@pytest.fixture(autouse=True)
def clean(monkeypatch):
    for name in ("_drafts", "_turns", "_ready", "_last_request"):
        monkeypatch.setattr(draft, name, {})
    monkeypatch.setattr(draft, "_sent", set())


class FakeAdmin:
    def __init__(self, escalate_error=None, recording="RECORDED", settle_errors=0):
        self.escalate_error = escalate_error
        self.recording = recording
        self.settle_errors = settle_errors
        self.records = {}
        self.escalations = []
        self.settled = []

    def escalate(self, first_name, last_name, car_number, start, end):
        if self.escalate_error:
            raise self.escalate_error
        request_id = f"RES-{len(self.escalations) + 1:06d}"
        self.escalations.append((first_name, last_name, car_number, start, end))
        self.records[request_id] = {"id": request_id, "status": "PENDING", "reason": ""}
        return SimpleNamespace(request_id=request_id)

    def get_decision(self, request_id):
        return self.records[request_id]

    def decide(self, request_id, status, reason=""):
        self.records[request_id] = {"id": request_id, "status": status, "reason": reason}

    def settle(self, request_id):
        self.settled.append(request_id)
        if self.settle_errors:
            self.settle_errors -= 1
            raise AdminServiceError("down")
        return self.records[request_id], self.recording


def chat_fn(session, message):
    if message == "book":
        draft.set_ready(session, dict(REQUEST))
        return "Submitted."
    return f"echo {message}"


def workflow(admin=None, **kwargs):
    admin = admin or FakeAdmin()
    return Workflow(chat_fn, admin, retry_delay=0, **kwargs), admin


def test_graph_has_the_expected_nodes():
    wf, _ = workflow()
    nodes = set(wf.graph.get_graph().nodes)
    assert {"chatbot", "escalate", "await_approval", "record", "notify"} <= nodes


def test_graph_can_be_drawn_for_the_documentation():
    wf, _ = workflow()
    assert "await_approval" in wf.graph.get_graph().draw_mermaid()


def test_a_normal_message_never_reaches_the_administrator():
    wf, admin = workflow()
    assert wf.send("s", "hello") == "echo hello"
    assert admin.escalations == []
    assert wf.waiting == 0


def test_a_confirmed_booking_is_escalated_and_the_id_is_returned():
    wf, admin = workflow()
    reply = wf.send("s", "book")
    assert "Submitted." in reply
    assert "RES-000001" in reply
    assert "NOT confirmed" in reply
    assert admin.escalations == [tuple(REQUEST.values())]
    assert wf.waiting == 1


def test_nothing_is_announced_while_the_administrator_has_not_decided():
    wf, _ = workflow()
    wf.send("s", "book")
    assert wf.poll() == []
    assert wf.waiting == 1


def test_approval_resumes_the_graph_records_and_notifies():
    wf, admin = workflow()
    wf.send("s", "book")
    admin.decide("RES-000001", "APPROVED", "see you then")

    notifications = wf.poll()

    assert len(notifications) == 1
    session, text = notifications[0]
    assert session == "s"
    assert "approved" in text
    assert "see you then" in text
    assert "now saved" in text
    assert admin.settled == ["RES-000001"]
    assert wf.waiting == 0


def test_a_refusal_is_notified_and_nothing_is_recorded():
    wf, admin = workflow()
    wf.send("s", "book")
    admin.decide("RES-000001", "REFUSED", "zone full")

    (_, text), = wf.poll()

    assert "refused" in text
    assert "approved" not in text
    assert admin.settled == []


def test_a_decision_is_announced_only_once():
    wf, admin = workflow()
    wf.send("s", "book")
    admin.decide("RES-000001", "APPROVED")
    assert len(wf.poll()) == 1
    assert wf.poll() == []


def test_an_unreachable_administrator_is_reported_and_nothing_waits():
    admin = FakeAdmin(escalate_error=AdminServiceError("down"))
    wf, _ = workflow(admin)
    reply = wf.send("s", "book")
    assert NOT_SENT in reply
    assert wf.waiting == 0
    assert draft.last_request("s") is None


def test_saving_is_retried_and_a_failure_is_reported():
    admin = FakeAdmin(recording="RECORD_FAILED")
    wf, _ = workflow(admin)
    wf.send("s", "book")
    admin.decide("RES-000001", "APPROVED")

    (_, text), = wf.poll()

    assert len(admin.settled) == 3
    assert "could not be saved" in text


def test_saving_succeeds_after_a_temporary_error():
    admin = FakeAdmin(settle_errors=1)
    wf, _ = workflow(admin)
    wf.send("s", "book")
    admin.decide("RES-000001", "APPROVED")

    (_, text), = wf.poll()

    assert len(admin.settled) == 2
    assert "now saved" in text


def test_two_bookings_in_one_session_are_tracked_separately():
    wf, admin = workflow()
    wf.send("s", "book")
    wf.send("s", "book")
    assert wf.waiting == 2
    admin.decide("RES-000001", "APPROVED")
    admin.decide("RES-000002", "REFUSED")
    assert len(wf.poll()) == 2
    assert wf.waiting == 0


def test_the_draft_is_cleared_and_the_id_remembered_after_escalation():
    draft._drafts["s"] = dict(REQUEST)
    wf, _ = workflow()
    wf.send("s", "book")
    assert draft.get_draft("s") == {}
    assert draft.last_request("s") == "RES-000001"


def reconcile_admin(outcomes):
    class Admin:
        client = SimpleNamespace(
            list_requests=lambda status: [{"id": key} for key in outcomes]
        )

        def settle(self, request_id):
            outcome = outcomes[request_id]
            if isinstance(outcome, Exception):
                raise outcome
            return {"id": request_id}, outcome

    return Admin()


def test_reconcile_saves_only_new_approved_bookings():
    admin = reconcile_admin(
        {"A": "RECORDED", "B": "ALREADY_RECORDED", "C": "RECORD_FAILED", "D": "NO_SPACE"}
    )
    assert Workflow(chat_fn, admin).reconcile() == 1


def test_reconcile_skips_a_booking_it_cannot_settle():
    admin = reconcile_admin(
        {"A": AdminServiceError("down"), "B": RecorderError("down"), "C": "RECORDED"}
    )
    assert Workflow(chat_fn, admin).reconcile() == 1