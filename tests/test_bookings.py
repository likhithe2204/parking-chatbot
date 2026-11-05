import sqlite3
from datetime import datetime

import pytest

from app import bookings
from app.seed_db import seed

START = "2026-12-10 10:00"
END = "2026-12-10 14:00"


@pytest.fixture
def db(tmp_path):
    path = tmp_path / "parking.db"
    seed(path)
    return path


def free(db, zone=None, start=START, end=END):
    return {r["zone"]: r["free_spaces"] for r in bookings.free_by_zone(start, end, zone, db)}


def test_free_spaces_equal_the_baseline_when_nothing_is_booked(db):
    assert free(db) == {"Zone A": 22, "Zone B": 35, "Zone C": 9}


def test_an_allocation_takes_one_space_in_the_chosen_zone(db):
    zone, created = bookings.allocate("RES-AAAAAA", "TS09AB1234", START, END, db)
    assert created is True
    assert zone == "Zone B"
    assert free(db) == {"Zone A": 22, "Zone B": 34, "Zone C": 9}


def test_the_zone_with_the_most_free_spaces_is_chosen_each_time(db):
    zones = [bookings.allocate(f"RES-{i:06d}", "TS09AB1234", START, END, db)[0] for i in range(14)]
    assert set(zones) == {"Zone B", "Zone A"}
    assert free(db)["Zone B"] + free(db)["Zone A"] + free(db)["Zone C"] == 22 + 35 + 9 - 14


def test_a_booking_does_not_affect_a_different_period(db):
    bookings.allocate("RES-AAAAAA", "TS09AB1234", START, END, db)
    assert free(db, start="2026-12-11 10:00", end="2026-12-11 14:00")["Zone B"] == 35


def test_back_to_back_bookings_do_not_overlap(db):
    bookings.allocate("RES-AAAAAA", "TS09AB1234", START, END, db)
    assert free(db, start=END, end="2026-12-10 18:00")["Zone B"] == 35


def test_an_overlapping_period_sees_the_booking(db):
    bookings.allocate("RES-AAAAAA", "TS09AB1234", START, END, db)
    assert free(db, start="2026-12-10 13:00", end="2026-12-10 16:00")["Zone B"] == 34


def test_repeating_an_allocation_changes_nothing(db):
    first = bookings.allocate("RES-AAAAAA", "TS09AB1234", START, END, db)
    second = bookings.allocate("res-aaaaaa", "TS09AB1234", START, END, db)
    assert first == ("Zone B", True)
    assert second == ("Zone B", False)
    assert free(db)["Zone B"] == 34


def test_a_full_period_raises_no_space(db):
    conn = sqlite3.connect(db)
    conn.execute("UPDATE availability SET available_spaces = 0")
    conn.commit()
    conn.close()
    with pytest.raises(bookings.NoSpaceAvailable):
        bookings.allocate("RES-AAAAAA", "TS09AB1234", START, END, db)
    assert free(db) == {"Zone A": 0, "Zone B": 0, "Zone C": 0}


def test_free_spaces_never_go_below_zero(db):
    conn = sqlite3.connect(db)
    conn.execute("UPDATE availability SET available_spaces = 1 WHERE zone = 'Zone C'")
    for i in range(3):
        conn.execute(
            "INSERT INTO bookings VALUES (?, 'Zone C', 'TS09AB1234', ?, ?)", (f"RES-{i}", START, END)
        )
    conn.commit()
    conn.close()
    assert free(db, zone="zone c") == {"Zone C": 0}


def test_a_database_without_the_bookings_table_still_answers(tmp_path):
    path = tmp_path / "old.db"
    seed(path)
    conn = sqlite3.connect(path)
    conn.execute("DROP TABLE bookings")
    conn.commit()
    conn.close()
    assert free(path) == {"Zone A": 22, "Zone B": 35, "Zone C": 9}


def test_the_window_for_now_is_one_minute_long():
    start, end = bookings.window_for_now(datetime(2026, 12, 10, 10, 30))
    assert (start, end) == ("2026-12-10 10:30", "2026-12-10 10:31")


def test_allocate_for_uses_the_admin_record(db):
    record = {"id": "RES-AAAAAA", "car_number": "TS09AB1234", "start": START, "end": END}
    assert bookings.allocate_for(record, db) == ("Zone B", True)