import pytest

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


def test_agent_has_four_tools():
    names = {t.name for t in TOOLS}
    assert names == {
        "search_parking_info",
        "check_working_hours",
        "check_prices",
        "check_availability",
    }