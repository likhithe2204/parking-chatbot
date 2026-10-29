import pytest

from app import reservation_file as rf

GOOD = dict(
    first_name="Likhith",
    last_name="Edupuganti",
    car_number="TS09AB1234",
    start="2026-12-05 10:00",
    end="2026-12-05 14:00",
    approval_time="2026-10-28 17:34:59",
)

EXPECTED = (
    "Likhith Edupuganti | TS09AB1234 | 2026-12-05 10:00 to 2026-12-05 14:00 "
    "| 2026-10-28 17:34:59"
)


def test_line_has_the_four_required_columns():
    assert rf.format_line(**GOOD) == EXPECTED
    assert len(rf.format_line(**GOOD).split(" | ")) == 4


def test_car_number_is_normalized():
    line = rf.format_line(**{**GOOD, "car_number": "ts 09 ab 1234"})
    assert line.split(" | ")[1] == "TS09AB1234"


def test_iso_approval_time_is_reformatted():
    line = rf.format_line(**{**GOOD, "approval_time": "2026-10-28T17:34:59"})
    assert line.endswith("| 2026-10-28 17:34:59")


def test_separator_character_in_a_name_is_rejected():
    with pytest.raises(rf.InvalidReservation):
        rf.format_line(**{**GOOD, "first_name": "Bob | Evil"})


def test_line_break_in_a_name_cannot_split_the_entry():
    line = rf.format_line(**{**GOOD, "first_name": "Bob\nEvil"})
    assert "\n" not in line
    assert line.startswith("Bob Evil Edupuganti | ")


def test_bad_car_number_is_rejected():
    with pytest.raises(rf.InvalidReservation):
        rf.format_line(**{**GOOD, "car_number": "ABC"})


def test_end_before_start_is_rejected():
    with pytest.raises(rf.InvalidReservation):
        rf.format_line(**{**GOOD, "end": "2026-12-05 09:00"})


def test_bad_approval_time_is_rejected():
    with pytest.raises(rf.InvalidReservation):
        rf.format_line(**{**GOOD, "approval_time": "yesterday"})


def test_append_creates_the_file_with_one_line(tmp_path):
    path = tmp_path / "data" / "reservations.txt"
    line, created = rf.append_reservation(**GOOD, path=path)
    assert created is True
    assert path.read_text(encoding="utf-8") == EXPECTED + "\n"
    assert line == EXPECTED


def test_the_same_reservation_is_not_written_twice(tmp_path):
    path = tmp_path / "reservations.txt"
    rf.append_reservation(**GOOD, path=path)
    _, created = rf.append_reservation(
        **{**GOOD, "approval_time": "2026-10-29 08:00:00"}, path=path
    )
    assert created is False
    assert len(path.read_text(encoding="utf-8").splitlines()) == 1


def test_a_different_period_is_a_new_entry(tmp_path):
    path = tmp_path / "reservations.txt"
    rf.append_reservation(**GOOD, path=path)
    _, created = rf.append_reservation(
        **{**GOOD, "start": "2026-12-06 10:00", "end": "2026-12-06 14:00"}, path=path
    )
    assert created is True
    assert len(path.read_text(encoding="utf-8").splitlines()) == 2