import re
from dataclasses import dataclass
from datetime import datetime, timedelta

DATETIME_FORMAT = "%Y-%m-%d %H:%M"
NAME_PATTERN = re.compile(r"^[A-Za-z][A-Za-z .'-]{0,49}$")
PLATE_PATTERN = re.compile(r"^[A-Z]{2}\d{1,2}[A-Z]{1,3}\d{4}$")
MAX_DURATION = timedelta(days=30)


@dataclass(frozen=True)
class ReservationRequest:
    first_name: str
    last_name: str
    car_number: str
    start: datetime
    end: datetime

    def summary(self) -> str:
        return (
            f"Name: {self.first_name} {self.last_name}\n"
            f"Car number: {self.car_number}\n"
            f"From: {self.start.strftime(DATETIME_FORMAT)}\n"
            f"To: {self.end.strftime(DATETIME_FORMAT)}"
        )


def _parse(value: str, label: str, errors: list[str]) -> datetime | None:
    try:
        return datetime.strptime(value.strip(), DATETIME_FORMAT)
    except ValueError:
        errors.append(f"{label} must be a date and time like 2026-10-28 10:00")
        return None


def validate_reservation(
    first_name: str,
    last_name: str,
    car_number: str,
    start: str,
    end: str,
    now: datetime | None = None,
) -> tuple[ReservationRequest | None, list[str]]:
    now = now or datetime.now()
    errors: list[str] = []

    first_name = " ".join(first_name.split())
    last_name = " ".join(last_name.split())
    plate = re.sub(r"[\s-]", "", car_number).upper()

    if not NAME_PATTERN.match(first_name):
        errors.append("First name must contain letters only")
    if not NAME_PATTERN.match(last_name):
        errors.append("Last name must contain letters only")
    if not PLATE_PATTERN.match(plate):
        errors.append("Car number must look like TS09AB1234")

    start_dt = _parse(start, "Start", errors)
    end_dt = _parse(end, "End", errors)

    if start_dt and end_dt:
        if start_dt <= now:
            errors.append("Start must be in the future")
        if end_dt <= start_dt:
            errors.append("End must be after the start")
        elif end_dt - start_dt > MAX_DURATION:
            errors.append("A reservation can be at most 30 days long")

    if errors:
        return None, errors

    return ReservationRequest(first_name, last_name, plate, start_dt, end_dt), [] 

def validate_field(
    field: str,
    value: str,
    start: str = "",
    now: datetime | None = None,
) -> tuple[str | None, str | None]:
    """Check one reservation field. Returns (normalized_value, error)."""
    now = now or datetime.now()

    if field in {"first_name", "last_name"}:
        name = " ".join(value.split())
        if NAME_PATTERN.match(name):
            return name, None
        return None, "Name must contain letters only"

    if field == "car_number":
        plate = re.sub(r"[\s-]", "", value).upper()
        if PLATE_PATTERN.match(plate):
            return plate, None
        return None, "Car number must look like TS09AB1234"

    if field in {"start", "end"}:
        errors: list[str] = []
        parsed = _parse(value, field.title(), errors)
        if parsed is None:
            return None, errors[0]
        if field == "start":
            if parsed <= now:
                return None, "Start must be in the future"
        elif start:
            start_dt = _parse(start, "Start", [])
            if start_dt and parsed <= start_dt:
                return None, "End must be after the start"
            if start_dt and parsed - start_dt > MAX_DURATION:
                return None, "A reservation can be at most 30 days long"
        elif parsed <= now:
            return None, "End must be in the future"
        return parsed.strftime(DATETIME_FORMAT), None

    return None, f"Unknown field '{field}'"