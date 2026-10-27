import pytest

from app import dynamic_data as dd
from app.seed_db import seed


@pytest.fixture
def db(tmp_path):
    path = tmp_path / "test.db"
    seed(path)
    return path


def test_availability_all_zones(db):
    assert len(dd.get_availability(db_path=db)) == 3


def test_availability_single_zone_is_case_insensitive(db):
    rows = dd.get_availability("zone c", db_path=db)
    assert rows[0]["available_spaces"] == 9


def test_prices_for_car(db):
    rows = dd.get_prices("car", db_path=db)
    assert rows[0]["hourly_rate"] == 40


def test_working_hours_for_monday(db):
    rows = dd.get_working_hours("monday", db_path=db)
    assert rows[0]["open_time"] == "06:00"


def test_unknown_zone_returns_empty_list(db):
    assert dd.get_availability("Zone Z", db_path=db) == []


def test_sql_injection_attempt_is_harmless(db):
    assert dd.get_availability("'; DROP TABLE availability; --", db_path=db) == []
    assert len(dd.get_availability(db_path=db)) == 3