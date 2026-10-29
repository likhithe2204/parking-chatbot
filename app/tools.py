from pathlib import Path

from langchain_core.runnables import RunnableConfig
from langchain_core.tools import tool

from app.admin_client import AdminServiceError
from app.draft import build_request, clear_draft, get_draft, save_field
from app.dynamic_data import get_availability, get_prices, get_working_hours
from app.rag import retrieve
from app.reservation import DATETIME_FORMAT
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


_admin_agent = None
_last_id: dict[str, str] = {}


def get_admin_agent():
    # Imported here because app.admin_agent itself imports from this module.
    global _admin_agent
    if _admin_agent is None:
        from app.admin_agent import AdminAgent

        _admin_agent = AdminAgent()
    return _admin_agent


def _thread_id(config: RunnableConfig) -> str:
    configurable = (config or {}).get("configurable", {})
    return configurable.get("thread_id", "default")


def _sent_message(request_id: str, summary: str) -> str:
    return (
        "STATUS: SENT_TO_ADMINISTRATOR\n"
        f"Request id: {request_id}\n"
        f"{summary}\n"
        "Tell the customer the request was sent to the administrator and is NOT "
        "confirmed yet. Give the request id and say they can ask for the status "
        "at any time. Never say it is approved."
    )


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
def save_reservation_detail(
    field: str, value: str, customer_words: str, config: RunnableConfig
) -> str:
    """Save ONE reservation detail the customer just gave.
    field must be one of: first_name, last_name, car_number, start, end.
    value is the detail in clean form (dates as YYYY-MM-DD HH:MM on a 24 hour
    clock). customer_words must be the exact words from the customer's latest
    message that contain this detail, copied letter for letter, and only the
    words for this one detail. Never guess or invent a detail. The reply tells
    you what to ask next."""
    return save_field(_thread_id(config), field, value, customer_words)


@tool
def submit_reservation_request(config: RunnableConfig) -> str:
    """Send the saved reservation request to the human administrator for approval.
    Call this only after all details are saved and the customer clearly confirmed
    the summary. This tool takes no arguments."""
    thread = _thread_id(config)
    request, errors = build_request(thread)

    if errors:
        if not get_draft(thread) and thread in _last_id:
            return (
                "STATUS: NOTHING_TO_SUBMIT\n"
                "No new reservation is waiting. The last request sent in this "
                f"conversation is {_last_id[thread]}. Do not send again. "
                "Tell the customer this request id."
            )
        return (
            "STATUS: INVALID\n- "
            + "\n- ".join(errors)
            + "\nTell the customer what is missing or wrong and collect it with "
            "save_reservation_detail."
        )

    try:
        escalation = get_admin_agent().escalate(
            request.first_name,
            request.last_name,
            request.car_number,
            request.start.strftime(DATETIME_FORMAT),
            request.end.strftime(DATETIME_FORMAT),
        )
    except AdminServiceError:
        return (
            "STATUS: ADMIN_UNAVAILABLE\n"
            "The request could not be sent to the administrator. Tell the customer "
            "it was NOT sent and to try again later. Do not say it is recorded or "
            "approved."
        )

    clear_draft(thread)
    _last_id[thread] = escalation.request_id
    return _sent_message(escalation.request_id, request.summary())


@tool
def check_reservation_status(request_id: str) -> str:
    """Check whether the administrator has approved or refused a reservation
    request. Pass the request id the customer was given, like RES-3F9A1C."""
    from app.admin_agent import decision_message

    try:
        record = get_admin_agent().get_decision(request_id.strip())
    except AdminServiceError as exc:
        if exc.status_code == 404:
            return "No request was found with that id. Ask the customer to check the id."
        return "The administrator service is not reachable right now. Ask the customer to try again later."
    return decision_message(record)


TOOLS = [
    search_parking_info,
    check_working_hours,
    check_prices,
    check_availability,
    save_reservation_detail,
    submit_reservation_request,
    check_reservation_status,
]