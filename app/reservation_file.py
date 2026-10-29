import os
import re
import threading
from datetime import datetime
from pathlib import Path

from app.config import RESERVATIONS_FILE
from app.reservation import DATETIME_FORMAT, NAME_PATTERN, PLATE_PATTERN

APPROVAL_FORMAT = "%Y-%m-%d %H:%M:%S"
SEPARATOR = " | "

_lock = threading.Lock()


class InvalidReservation(ValueError):
    pass


def _name(value: str, label: str) -> str:
    cleaned = " ".join(str(value).split())
    if not NAME_PATTERN.match(cleaned):
        raise InvalidReservation(f"{label} must contain letters only")
    return cleaned


def _slot(value: str, label: str) -> datetime:
    try:
        return datetime.strptime(str(value).strip(), DATETIME_FORMAT)
    except ValueError:
        raise InvalidReservation(f"{label} must look like 2026-12-05 10:00") from None


def _approval(value: str) -> str:
    try:
        parsed = datetime.fromisoformat(str(value).strip())
    except ValueError:
        raise InvalidReservation("Approval time must be a date and time") from None
    if parsed.tzinfo is not None:
        raise InvalidReservation("Approval time must not carry a time zone")
    return parsed.strftime(APPROVAL_FORMAT)


def format_line(
    first_name: str,
    last_name: str,
    car_number: str,
    start: str,
    end: str,
    approval_time: str,
) -> str:
    first = _name(first_name, "First name")
    last = _name(last_name, "Last name")
    plate = re.sub(r"[\s-]", "", str(car_number)).upper()
    if not PLATE_PATTERN.match(plate):
        raise InvalidReservation("Car number must look like TS09AB1234")

    start_dt = _slot(start, "Start")
    end_dt = _slot(end, "End")
    if end_dt <= start_dt:
        raise InvalidReservation("End must be after the start")

    period = f"{start_dt.strftime(DATETIME_FORMAT)} to {end_dt.strftime(DATETIME_FORMAT)}"
    return SEPARATOR.join([f"{first} {last}", plate, period, _approval(approval_time)])


def append_reservation(
    first_name: str,
    last_name: str,
    car_number: str,
    start: str,
    end: str,
    approval_time: str,
    path=RESERVATIONS_FILE,
) -> tuple[str, bool]:
    """Append one reservation line. Returns (line, created); created is False
    when the same name, car and period are already in the file."""
    line = format_line(first_name, last_name, car_number, start, end, approval_time)
    identity = line.rsplit(SEPARATOR, 1)[0] + SEPARATOR

    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    with _lock:
        if target.exists():
            with target.open(encoding="utf-8") as handle:
                if any(existing.startswith(identity) for existing in handle):
                    return line, False
        with target.open("a", encoding="utf-8", newline="\n") as handle:
            handle.write(line + "\n")
            handle.flush()
            os.fsync(handle.fileno())
    return line, True