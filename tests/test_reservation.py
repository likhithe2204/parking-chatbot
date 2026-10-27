from datetime import datetime

from app.reservation import validate_field, validate_reservation

NOW = datetime(2026, 10, 27, 12, 0)

GOOD = {
    "first_name": "Likhith",
    "last_name": "Edupuganti",
    "car_number": "TS09AB1234",
    "start": "2026-10-28 10:00",
    "end": "2026-10-28 14:00",
}


def test_valid_request_is_accepted():
    request, errors = validate_reservation(**GOOD, now=NOW)
    assert errors == []
    assert request.car_number == "TS09AB1234"


def test_car_number_is_normalized():
    request, errors = validate_reservation(**{**GOOD, "car_number": "ts 09 ab 1234"}, now=NOW)
    assert errors == []
    assert request.car_number == "TS09AB1234"


def test_bad_car_number_is_rejected():
    request, errors = validate_reservation(**{**GOOD, "car_number": "12345"}, now=NOW)
    assert request is None
    assert any("Car number" in e for e in errors)


def test_end_before_start_is_rejected():
    _, errors = validate_reservation(
        **{**GOOD, "start": "2026-10-28 14:00", "end": "2026-10-28 10:00"}, now=NOW
    )
    assert any("End must be after" in e for e in errors)


def test_start_in_the_past_is_rejected():
    _, errors = validate_reservation(**{**GOOD, "start": "2026-10-01 10:00"}, now=NOW)
    assert any("future" in e for e in errors)


def test_name_with_digits_is_rejected():
    _, errors = validate_reservation(**{**GOOD, "first_name": "Lik123"}, now=NOW)
    assert any("First name" in e for e in errors)


def test_bad_date_format_is_rejected():
    _, errors = validate_reservation(**{**GOOD, "start": "tomorrow"}, now=NOW)
    assert any("Start must be" in e for e in errors)

def test_field_rejects_bad_car_number():
    value, error = validate_field("car_number", "ABC", now=NOW)
    assert value is None
    assert "TS09AB1234" in error


def test_field_normalizes_good_car_number():
    value, error = validate_field("car_number", "ts 09 ab 1234", now=NOW)
    assert (value, error) == ("TS09AB1234", None)


def test_field_end_must_follow_start():
    _, error = validate_field(
        "end", "2026-10-28 09:00", start="2026-10-28 10:00", now=NOW
    )
    assert "after the start" in error


def test_field_start_in_past_is_rejected():
    _, error = validate_field("start", "2026-10-01 10:00", now=NOW)
    assert "future" in error