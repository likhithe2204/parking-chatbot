from types import SimpleNamespace

import pytest

from app import agent, draft

SUMMARY = (
    "Please confirm the reservation details:\n"
    "Car number: TS09AB1234\n"
    "From: 2026-10-30 10:00\n"
    "To: 2026-10-30 18:00\n"
    "Shall I submit this request? (yes / no)"
)

PARTIAL = {"first_name": "Likhith", "last_name": "Edupuganti", "car_number": "TS09AB1234"}


def full(start="2026-10-30 10:00", end="2026-10-30 18:00"):
    return {**PARTIAL, "start": start, "end": end}


@pytest.fixture(autouse=True)
def clean(monkeypatch):
    monkeypatch.setattr(draft, "_drafts", {})
    monkeypatch.setattr(draft, "_turns", {})
    monkeypatch.setattr(draft, "_sent", set())


class ScriptedAgent:
    def __init__(self, replies):
        self.replies = list(replies)
        self.sent = []

    def invoke(self, payload, config=None):
        self.sent.append(payload["messages"][0]["content"])
        return {"messages": [SimpleNamespace(content=self.replies.pop(0))]}


def test_summary_with_missing_details_is_a_problem():
    draft._drafts["g"] = dict(PARTIAL)
    problem = draft.reply_problem("g", SUMMARY)
    assert "start" in problem
    assert "end" in problem


def test_ordinary_replies_are_not_a_problem():
    draft._drafts["g"] = dict(PARTIAL)
    assert draft.reply_problem("g", "Please tell me your car number, like TS09AB1234.") is None
    assert draft.reply_problem("g", "Reservations are confirmed by an administrator.") is None


def test_matching_summary_is_accepted():
    draft._drafts["g"] = full()
    assert draft.reply_problem("g", SUMMARY) is None


def test_summary_with_other_dates_is_a_problem():
    draft._drafts["g"] = full("2026-12-05 10:00", "2026-12-05 14:00")
    assert "does not match" in draft.reply_problem("g", SUMMARY)


def test_reply_after_sending_is_not_flagged():
    draft._drafts["g"] = full()
    draft.clear_draft("g")
    assert draft.reply_problem("g", SUMMARY) is None


def test_safe_reply_asks_for_the_first_missing_detail():
    draft._drafts["g"] = dict(PARTIAL)
    assert "start date" in draft.safe_reply("g")


def test_safe_reply_shows_only_the_saved_details():
    draft._drafts["g"] = full("2026-12-05 10:00", "2026-12-05 14:00")
    text = draft.safe_reply("g")
    assert "2026-12-05 10:00" in text
    assert "2026-10-30" not in text


def test_fabricated_summary_is_corrected_by_a_retry():
    draft._drafts["c1"] = dict(PARTIAL)
    fake = ScriptedAgent([SUMMARY, "Please tell me the start date and time."])
    reply = agent.chat(fake, "TS09AB1234", thread_id="c1")
    assert reply.startswith("Please tell me the start")
    assert "SYSTEM CHECK" in fake.sent[1]


def test_a_second_bad_reply_is_replaced_by_the_safe_message():
    draft._drafts["c2"] = dict(PARTIAL)
    fake = ScriptedAgent([SUMMARY, SUMMARY])
    reply = agent.chat(fake, "TS09AB1234", thread_id="c2")
    assert "2026-10-30" not in reply
    assert "start" in reply.lower()


def test_a_good_reply_is_not_retried():
    draft._drafts["c3"] = dict(PARTIAL)
    fake = ScriptedAgent(["Please tell me the start date and time."])
    agent.chat(fake, "TS09AB1234", thread_id="c3")
    assert len(fake.sent) == 1