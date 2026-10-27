from pathlib import Path

from langchain_core.tools import tool

from app.dynamic_data import get_availability, get_prices, get_working_hours
from app.rag import retrieve
from app.seed_db import DB_PATH
from app.reservation import validate_field, validate_reservation


def format_availability(zone: str = "", db_path: Path = DB_PATH) -> str:
    rows = get_availability(zone or None, db_path=db_path)
    if not rows:
        return f"No zone found for '{zone}'. Valid zones are Zone A, Zone B and Zone C."
    return "\n".join(
        f"{r['zone']}: {r['available_spaces']} of {r['total_spaces']} spaces available"
        for r in rows
    )


def format_prices(vehicle_type: str = "", db_path: Path = DB_PATH) -> str:
    rows = get_prices(vehicle_type or None, db_path=db_path)
    if not rows:
        return f"No prices found for '{vehicle_type}'. Valid types are car, two wheeler and ev car."
    return "\n".join(
        f"{r['vehicle_type']}: INR {r['hourly_rate']} per hour, INR {r['daily_rate']} per day"
        for r in rows
    )


def format_working_hours(day: str = "", db_path: Path = DB_PATH) -> str:
    rows = get_working_hours(day or None, db_path=db_path)
    if not rows:
        return f"No working hours found for '{day}'. Use a weekday name like Monday."
    return "\n".join(f"{r['day']}: {r['open_time']} to {r['close_time']}" for r in rows)


@tool
def search_parking_info(query: str) -> str:
    """Search general information, parking details, location, zones, EV charging,
    booking process and cancellation rules. Use this for any question about the
    facility that is not prices, working hours or live availability."""
    docs = retrieve(query, k=3)
    return "\n\n".join(d.page_content for d in docs)


@tool
def check_working_hours(day: str = "") -> str:
    """Get the opening and closing time. Pass a weekday name like 'Monday',
    or leave empty to get all days."""
    return format_working_hours(day)


@tool
def check_prices(vehicle_type: str = "") -> str:
    """Get parking prices per hour and per day. Pass 'car', 'two wheeler' or
    'ev car', or leave empty to get all vehicle types."""
    return format_prices(vehicle_type)


@tool
def check_availability(zone: str = "") -> str:
    """Get the number of free parking spaces right now. Pass 'Zone A', 'Zone B'
    or 'Zone C', or leave empty to get all zones."""
    return format_availability(zone)

@tool
def submit_reservation_request(
    first_name: str, last_name: str, car_number: str, start: str, end: str
) -> str:
    """Validate and record a reservation request. Call this only after the
    customer has confirmed all details. Start and end must be in the format
    YYYY-MM-DD HH:MM (24 hour clock)."""
    request, errors = validate_reservation(first_name, last_name, car_number, start, end)
    if errors:
        return (
            "STATUS: INVALID\n- "
            + "\n- ".join(errors)
            + "\nTell the customer what to fix and ask only for those fields."
        )
    return (
        "STATUS: READY_FOR_ADMIN_REVIEW\n"
        + request.summary()
        + "\nTell the customer the details are recorded and will be sent to the "
        "administrator for approval. Do not say the booking is confirmed."
    )

@tool
def check_reservation_field(field: str, value: str, start: str = "") -> str:
    """Validate ONE reservation detail right after the customer gives it.
    field must be one of: first_name, last_name, car_number, start, end.
    Dates use the format YYYY-MM-DD HH:MM. When checking 'end', also pass the
    already collected start value in 'start'."""
    normalized, error = validate_field(field, value, start)
    if error:
        return f"INVALID: {error}. Ask the customer to provide {field} again."
    return f"VALID: {normalized}"

TOOLS = [
    search_parking_info,
    check_working_hours,
    check_prices,
    check_availability,
    check_reservation_field,
    submit_reservation_request,
]