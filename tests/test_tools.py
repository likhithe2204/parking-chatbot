import pytest

from app import bookings
from app.seed_db import seed
from app.tools import (
    TOOLS,
    format_availability,
    format_prices,
    format_working_hours,
)


@pytest.fixture
def db(tmp_path):
    path = tmp_path / "test.db"
    seed(path)
    return path


def test_availability_all_zones(db):
    text = format_availability(db_path=db)
    assert "Zone A: 22 of 60 spaces available" in text
    assert "Zone C: 9 of 40 spaces available" in text


def test_availability_unknown_zone_gives_helpful_message(db):
    assert "No zone found" in format_availability("Zone Z", db_path=db)


def test_prices_for_car(db):
    assert "INR 40 per hour" in format_prices("car", db_path=db)


def test_prices_unknown_vehicle(db):
    assert "No prices found" in format_prices("helicopter", db_path=db)


def test_working_hours_monday(db):
    assert "Monday: 06:00 to 23:00" in format_working_hours("monday", db_path=db)



def test_agent_has_seven_tools():
    names = {t.name for t in TOOLS}
    assert names == {
        "search_parking_info",
        "check_working_hours",
        "check_prices",
        "check_availability",
        "save_reservation_detail",
        "submit_reservation_request",
        "check_reservation_status",
    }

def test_availability_without_a_period_says_it_is_for_right_now(db):
    assert "right now" in format_availability(db_path=db)


def test_availability_for_a_period_drops_after_a_booking(db):
    bookings.allocate("RES-AAAAAA", "TS09AB1234", "2026-12-10 10:00", "2026-12-10 14:00", db)
    text = format_availability("Zone B", "2026-12-10 10:00", "2026-12-10 14:00", db_path=db)
    assert "Zone B: 34 of 80 spaces available" in text
    assert "for 2026-12-10 10:00 to 2026-12-10 14:00" in text


def test_availability_for_another_period_is_unchanged(db):
    bookings.allocate("RES-AAAAAA", "TS09AB1234", "2026-12-10 10:00", "2026-12-10 14:00", db)
    text = format_availability("Zone B", "2026-12-11 10:00", "2026-12-11 14:00", db_path=db)
    assert "Zone B: 35 of 80 spaces available" in text


def test_availability_needs_both_dates(db):
    assert "both a start and an end" in format_availability(start="2026-12-10 10:00", db_path=db)


def test_availability_rejects_bad_dates(db):
    text = format_availability(start="tomorrow", end="later", db_path=db)
    assert "YYYY-MM-DD HH:MM" in text
    assert "The end must be after the start" in format_availability(
        start="2026-12-10 14:00", end="2026-12-10 10:00", db_path=db
    )