import pytest

from app import draft, tools
from app.admin_agent import Escalation
from app.admin_client import AdminServiceError

CONFIG = {"configurable": {"thread_id": "t1"}}

DETAILS = [
    ("first_name", "Likhith"),
    ("last_name", "Edupuganti"),
    ("car_number", "TS09AB1234"),
    ("start", "2099-01-01 10:00"),
    ("end", "2099-01-01 12:00"),
]


class FakeAdminAgent:
    def __init__(self, error=None, record=None):
        self.error = error
        self.record = record or {"id": "RES-AAAAAA", "status": "PENDING", "reason": ""}
        self.calls = []

    def escalate(self, first_name, last_name, car_number, start, end):
        self.calls.append((first_name, last_name, car_number, start, end))
        if self.error:
            raise self.error
        return Escalation("RES-AAAAAA", "note", {"id": "RES-AAAAAA", "status": "PENDING"})

    def get_decision(self, request_id):
        if self.error:
            raise self.error
        return self.record


@pytest.fixture(autouse=True)
def clean_state(monkeypatch):
    monkeypatch.setattr(draft, "_drafts", {})
    monkeypatch.setattr(draft, "_turns", {})
    monkeypatch.setattr(tools, "_last_id", {})


def use_agent(monkeypatch, agent):
    monkeypatch.setattr(tools, "get_admin_agent", lambda: agent)
    return agent


def save(field, value):
    draft.begin_turn("t1", value)
    return tools.save_reservation_detail.invoke(
        {"field": field, "value": value, "customer_words": value}, config=CONFIG
    )


def fill_draft():
    for field, value in DETAILS:
        save(field, value)


def submit():
    return tools.submit_reservation_request.invoke({}, config=CONFIG)


def test_save_tool_tells_the_agent_what_to_ask_next():
    result = save("first_name", "Likhith")
    assert "NEXT" in result
    assert "last name" in result


def test_submit_with_missing_details_is_rejected(monkeypatch):
    agent = use_agent(monkeypatch, FakeAdminAgent())
    save("first_name", "Likhith")
    result = submit()
    assert "INVALID" in result
    assert "Missing details" in result
    assert agent.calls == []


def test_complete_request_is_sent_and_the_id_is_returned(monkeypatch):
    agent = use_agent(monkeypatch, FakeAdminAgent())
    fill_draft()
    result = submit()
    assert "SENT_TO_ADMINISTRATOR" in result
    assert "RES-AAAAAA" in result
    assert len(agent.calls) == 1


def test_the_same_request_is_not_sent_twice(monkeypatch):
    agent = use_agent(monkeypatch, FakeAdminAgent())
    fill_draft()
    submit()
    second = submit()
    assert len(agent.calls) == 1
    assert "NOTHING_TO_SUBMIT" in second
    assert "RES-AAAAAA" in second


def test_draft_is_cleared_after_sending(monkeypatch):
    use_agent(monkeypatch, FakeAdminAgent())
    fill_draft()
    submit()
    assert draft.get_draft("t1") == {}


def test_unreachable_administrator_is_never_reported_as_success(monkeypatch):
    use_agent(monkeypatch, FakeAdminAgent(error=AdminServiceError("down")))
    fill_draft()
    result = submit()
    assert "ADMIN_UNAVAILABLE" in result
    assert "SENT_TO_ADMINISTRATOR" not in result
    assert len(draft.get_draft("t1")) == 5


def test_status_of_an_approved_request(monkeypatch):
    record = {"id": "RES-AAAAAA", "status": "APPROVED", "reason": "see you then"}
    use_agent(monkeypatch, FakeAdminAgent(record=record))
    result = tools.check_reservation_status.invoke({"request_id": "RES-AAAAAA"})
    assert "approved" in result
    assert "see you then" in result


def test_status_of_a_pending_request(monkeypatch):
    use_agent(monkeypatch, FakeAdminAgent())
    result = tools.check_reservation_status.invoke({"request_id": "RES-AAAAAA"})
    assert "still waiting" in result


def test_status_of_an_unknown_request(monkeypatch):
    error = AdminServiceError("not found", status_code=404)
    use_agent(monkeypatch, FakeAdminAgent(error=error))
    result = tools.check_reservation_status.invoke({"request_id": "RES-NOPE00"})
    assert "No request was found" in result


def test_status_when_the_service_is_unreachable(monkeypatch):
    use_agent(monkeypatch, FakeAdminAgent(error=AdminServiceError("down")))
    result = tools.check_reservation_status.invoke({"request_id": "RES-AAAAAA"})
    assert "not reachable" in result

def test_save_tool_rejects_words_the_customer_did_not_say():
    draft.begin_turn("t1", "TS09AB1234")
    result = tools.save_reservation_detail.invoke(
        {
            "field": "start",
            "value": "2099-01-01 10:00",
            "customer_words": "2099-01-01 10:00",
        },
        config=CONFIG,
    )
    assert result.startswith("INVALID")