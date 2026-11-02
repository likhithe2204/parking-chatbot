import pytest

from app import draft, tools
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
        self.settled = []

    def get_decision(self, request_id):
        if self.error:
            raise self.error
        return self.record

    def settle(self, request_id):
        self.settled.append(request_id)
        return self.record, "RECORDED"


@pytest.fixture(autouse=True)
def clean_state(monkeypatch):
    for name in ("_drafts", "_turns", "_ready", "_last_request"):
        monkeypatch.setattr(draft, name, {})
    monkeypatch.setattr(draft, "_sent", set())


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


def test_submit_with_missing_details_is_rejected():
    save("first_name", "Likhith")
    result = submit()
    assert "INVALID" in result
    assert "Missing details" in result
    assert draft.take_ready("t1") is None


def test_a_complete_request_is_handed_to_the_workflow():
    fill_draft()
    result = submit()
    assert "SUBMITTED" in result
    assert "NOT confirmed" in result
    assert draft.take_ready("t1") == {
        "first_name": "Likhith",
        "last_name": "Edupuganti",
        "car_number": "TS09AB1234",
        "start": "2099-01-01 10:00",
        "end": "2099-01-01 12:00",
    }


def test_submitting_again_after_sending_reports_the_existing_request():
    fill_draft()
    submit()
    draft.take_ready("t1")
    draft.clear_draft("t1")
    draft.remember_request("t1", "RES-AAAAAA")

    result = submit()

    assert "NOTHING_TO_SUBMIT" in result
    assert "RES-AAAAAA" in result


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


def test_a_status_check_never_saves_a_booking(monkeypatch):
    record = {"id": "RES-AAAAAA", "status": "APPROVED", "reason": ""}
    agent = use_agent(monkeypatch, FakeAdminAgent(record=record))
    tools.check_reservation_status.invoke({"request_id": "RES-AAAAAA"})
    assert agent.settled == []