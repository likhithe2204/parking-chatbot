from datetime import datetime

import pytest

from app import draft

NOW = datetime(2026, 10, 28, 12, 0)

FULL = [
    ("first_name", "Likhith"),
    ("last_name", "Edupuganti"),
    ("car_number", "ts09ab1234"),
    ("start", "2099-01-01 10:00"),
    ("end", "2099-01-01 12:00"),
]


@pytest.fixture(autouse=True)
def clean(monkeypatch):
    monkeypatch.setattr(draft, "_drafts", {})
    monkeypatch.setattr(draft, "_turns", {})


def turn(message, thread="t"):
    draft.begin_turn(thread, message)


def save(field, value, said=None, thread="t"):
    return draft.save_field(thread, field, value, said or value, now=NOW)


def fill(thread="t"):
    result = ""
    for field, value in FULL:
        turn(value, thread)
        result = save(field, value, thread=thread)
    return result


def test_first_name_is_followed_by_a_request_for_the_last_name():
    turn("Likhith")
    result = save("first_name", "Likhith")
    assert result.startswith("SAVED")
    assert "last name" in result


def test_detail_not_in_the_customers_message_is_rejected():
    turn("TS09AB1234")
    result = save("start", "2099-01-01 10:00")
    assert result.startswith("INVALID")
    assert "not in the customer's latest message" in result
    assert "start" not in draft.get_draft("t")


def test_invented_dates_cannot_ride_on_another_answer():
    turn("TS09AB1234")
    assert save("car_number", "TS09AB1234").startswith("SAVED")
    result = save("start", "2099-01-01 10:00", said="TS09AB1234")
    assert result.startswith("INVALID")
    assert "start" not in draft.get_draft("t")


def test_a_quote_without_a_time_clue_cannot_support_a_date():
    turn("whenever")
    result = save("start", "2099-01-01 10:00", said="whenever")
    assert result.startswith("INVALID")
    assert "start" not in draft.get_draft("t")


def test_name_must_appear_in_the_customers_words():
    turn("TS09AB1234")
    result = save("first_name", "Rahul", said="TS09AB1234")
    assert result.startswith("INVALID")
    assert "first_name" not in draft.get_draft("t")


def test_two_details_in_one_message_are_both_saved():
    turn("Likhith Edupuganti")
    assert save("first_name", "Likhith", said="Likhith").startswith("SAVED")
    assert save("last_name", "Edupuganti", said="Edupuganti").startswith("SAVED")


def test_relative_date_words_are_accepted():
    turn("tomorrow 10am")
    result = save("start", "2099-01-01 10:00", said="tomorrow 10am")
    assert result.startswith("SAVED")


def test_end_cannot_be_saved_before_the_start():
    turn("2099-01-01 12:00")
    result = save("end", "2099-01-01 12:00")
    assert result.startswith("INVALID")
    assert "start" in result
    assert "end" not in draft.get_draft("t")


def test_invalid_value_is_rejected_and_not_stored():
    turn("ABC")
    result = save("car_number", "ABC")
    assert result.startswith("INVALID")
    assert "car_number" not in draft.get_draft("t")


def test_start_in_the_past_is_rejected():
    turn("2026-10-01 10:00")
    result = save("start", "2026-10-01 10:00")
    assert result.startswith("INVALID")
    assert "future" in result


def test_all_five_details_complete_the_draft():
    result = fill()
    assert "ALL_DETAILS_COLLECTED" in result
    assert "TS09AB1234" in result
    assert draft.missing_fields(draft.get_draft("t")) == []


def test_changing_the_start_drops_an_end_that_no_longer_fits():
    fill()
    turn("2099-03-01 10:00")
    save("start", "2099-03-01 10:00")
    assert "end" not in draft.get_draft("t")


def test_incomplete_draft_cannot_become_a_request():
    turn("Likhith")
    save("first_name", "Likhith")
    request, errors = draft.build_request("t", now=NOW)
    assert request is None
    assert "Missing details" in errors[0]


def test_complete_draft_becomes_a_request():
    fill()
    request, errors = draft.build_request("t", now=NOW)
    assert errors == []
    assert request.car_number == "TS09AB1234"


def test_conversations_have_separate_drafts():
    turn("Likhith", "a")
    save("first_name", "Likhith", thread="a")
    assert draft.get_draft("b") == {}


def test_unknown_field_is_rejected():
    assert save("email", "x@y.com").startswith("INVALID")