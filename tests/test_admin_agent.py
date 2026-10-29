import pytest
from langchain_core.language_models.fake_chat_models import GenericFakeChatModel
from langchain_core.messages import AIMessage

from app.admin_agent import AdminAgent, decision_message
from app.admin_client import AdminServiceError

DETAILS = dict(
    first_name="Likhith",
    last_name="Edupuganti",
    car_number="TS09AB1234",
    start="2099-01-01 10:00",
    end="2099-01-01 12:00",
)


class ScriptedModel(GenericFakeChatModel):
    def bind_tools(self, tools, **kwargs):
        return self


class BrokenModel(GenericFakeChatModel):
    def bind_tools(self, tools, **kwargs):
        raise RuntimeError("llm down")


def scripted(*messages):
    return ScriptedModel(messages=iter(messages))


def send_note(note):
    return AIMessage(
        content="",
        tool_calls=[
            {"name": "send_to_administrator", "args": {"note": note}, "id": "call-1"}
        ],
    )


class FakeClient:
    def __init__(self, fail=False):
        self.fail = fail
        self.submitted = []

    def submit_request(self, first_name, last_name, car_number, start, end, note=""):
        if self.fail:
            raise AdminServiceError("service down")
        entry = dict(
            first_name=first_name,
            last_name=last_name,
            car_number=car_number,
            start=start,
            end=end,
            note=note,
        )
        self.submitted.append(entry)
        return {"id": "RES-AAAAAA", "status": "PENDING", **entry}

    def get_request(self, request_id):
        return {"id": request_id, "status": "APPROVED", "reason": ""}


def test_agent_sends_the_exact_customer_details_with_its_note():
    client = FakeClient()
    note = "Customer asks for 2 hours. Zone B has free spaces."
    model = scripted(send_note(note), AIMessage(content="DONE"))

    result = AdminAgent(client=client, llm=model).escalate(**DETAILS)

    assert client.submitted == [{**DETAILS, "note": note}]
    assert result.request_id == "RES-AAAAAA"
    assert result.note == note


def test_request_is_still_sent_when_the_model_fails():
    client = FakeClient()
    model = BrokenModel(messages=iter([]))

    result = AdminAgent(client=client, llm=model).escalate(**DETAILS)

    assert len(client.submitted) == 1
    assert "TS09AB1234" in client.submitted[0]["note"]
    assert result.request_id == "RES-AAAAAA"


def test_request_is_still_sent_when_the_model_skips_the_tool():
    client = FakeClient()
    model = scripted(AIMessage(content="DONE"))

    AdminAgent(client=client, llm=model).escalate(**DETAILS)

    assert len(client.submitted) == 1
    assert "Likhith Edupuganti" in client.submitted[0]["note"]


def test_unreachable_admin_service_is_reported():
    client = FakeClient(fail=True)
    model = scripted(send_note("note"), AIMessage(content="DONE"))

    with pytest.raises(AdminServiceError):
        AdminAgent(client=client, llm=model).escalate(**DETAILS)


def test_get_decision_returns_the_stored_record():
    agent = AdminAgent(client=FakeClient(), llm=None)
    assert agent.get_decision("RES-AAAAAA")["status"] == "APPROVED"


def test_pending_message():
    text = decision_message({"id": "RES-AAAAAA", "status": "PENDING"})
    assert "still waiting" in text


def test_approved_message_includes_the_reason():
    text = decision_message({"id": "RES-AAAAAA", "status": "APPROVED", "reason": "see you then"})
    assert "approved" in text
    assert "see you then" in text


def test_refused_message_is_never_worded_as_an_approval():
    text = decision_message({"id": "RES-AAAAAA", "status": "REFUSED", "reason": "zone full"})
    assert "refused" in text
    assert "approved" not in text