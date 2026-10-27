from pathlib import Path

from langchain_core.tools import tool

from app.dynamic_data import get_availability, get_prices, get_working_hours
from app.rag import retrieve
from app.seed_db import DB_PATH


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


TOOLS = [search_parking_info, check_working_hours, check_prices, check_availability]