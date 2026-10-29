import re
from datetime import datetime

from app.reservation import validate_field, validate_reservation

FIELDS = ("first_name", "last_name", "car_number", "start", "end")

PROMPTS = {
    "first_name": "the customer's first name",
    "last_name": "the customer's last name",
    "car_number": "the car number, like TS09AB1234",
    "start": "the start date and time, format YYYY-MM-DD HH:MM (24 hour clock)",
    "end": "the end date and time, format YYYY-MM-DD HH:MM (24 hour clock)",
}

_MONTHS = r"(?:jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)[a-z]*"
TIME_CLUE = re.compile(
    "|".join(
        [
            r"\d{1,2}:\d{2}",
            r"\d{4}-\d{2}-\d{2}",
            r"\b\d{1,2}\s*(?:am|pm)\b",
            r"\b(?:today|tomorrow|tonight|noon|midnight|monday|tuesday|wednesday|thursday|friday|saturday|sunday)\b",
            rf"\b\d{{1,2}}(?:st|nd|rd|th)?\s*{_MONTHS}\b",
            rf"\b{_MONTHS}\s*\d{{1,2}}\b",
        ]
    ),
    re.IGNORECASE,
)

_drafts: dict[str, dict[str, str]] = {}
_turns: dict[str, dict] = {}
_sent: set[str] = set()


def _norm(text: str) -> str:
    return " ".join(text.lower().split())


def begin_turn(thread_id: str, message: str) -> None:
    _turns[thread_id] = {"message": _norm(message), "used": []}


def get_draft(thread_id: str) -> dict[str, str]:
    return dict(_drafts.get(thread_id, {}))


def clear_draft(thread_id: str) -> None:
    _drafts.pop(thread_id, None)
    _sent.add(thread_id)


def missing_fields(draft: dict) -> list[str]:
    return [field for field in FIELDS if field not in draft]


def summary(draft: dict) -> str:
    return (
        f"Name: {draft['first_name']} {draft['last_name']}, "
        f"Car number: {draft['car_number']}, "
        f"From: {draft['start']}, To: {draft['end']}"
    )


def next_prompt(draft: dict) -> str:
    missing = missing_fields(draft)
    if not missing:
        return (
            "ALL_DETAILS_COLLECTED. Show the customer this summary and ask them "
            f"to confirm: {summary(draft)}"
        )
    return (
        f"NEXT: ask the customer for {PROMPTS[missing[0]]}. "
        "Ask for this one detail only."
    )


def _supported(field: str, value: str, said: str) -> bool:
    if field in ("first_name", "last_name"):
        return _norm(value) in _norm(said)
    if field == "car_number":
        return value in re.sub(r"[\s-]", "", said).upper()
    return bool(TIME_CLUE.search(said))


def save_field(
    thread_id: str, field: str, value: str, said: str, now: datetime | None = None
) -> str:
    if field not in FIELDS:
        return f"INVALID: unknown field '{field}'. Valid fields are {', '.join(FIELDS)}."

    draft = _drafts.get(thread_id, {})
    turn = _turns.get(thread_id)
    quote = _norm(said or "")

    if not turn or not quote or quote not in turn["message"]:
        return (
            "INVALID: those words are not in the customer's latest message. "
            "Never guess or invent a detail. " + next_prompt(draft)
        )
    if any(quote in used or used in quote for used in turn["used"]):
        return (
            "INVALID: those words were already used for another detail. "
            + next_prompt(draft)
        )
    if field == "end" and "start" not in draft:
        return "INVALID: the start must be saved before the end. " + next_prompt(draft)

    normalized, error = validate_field(
        field, value, start=draft.get("start", ""), now=now
    )
    if error:
        return f"INVALID: {error}. Ask the customer for {PROMPTS[field]} again."
    if not _supported(field, normalized, said):
        return (
            f"INVALID: the customer's words do not contain that {field.replace('_', ' ')}. "
            "Never guess or invent a detail. " + next_prompt(draft)
        )

    draft = _drafts.setdefault(thread_id, {})
    _sent.discard(thread_id)
    turn["used"].append(quote)
    draft[field] = normalized
    if field == "start" and "end" in draft:
        _, end_error = validate_field("end", draft["end"], start=normalized, now=now)
        if end_error:
            del draft["end"]
    return "SAVED. " + next_prompt(draft)


def build_request(thread_id: str, now: datetime | None = None):
    draft = _drafts.get(thread_id, {})
    missing = missing_fields(draft)
    if missing:
        return None, [f"Missing details: {', '.join(missing)}"]
    return validate_reservation(
        draft["first_name"],
        draft["last_name"],
        draft["car_number"],
        draft["start"],
        draft["end"],
        now=now,
    )

CONFIRM_WORDS = (
    "please confirm",
    "shall i submit",
    "confirm the reservation",
    "confirm these",
    "submit this request",
)
DATE_IN_TEXT = re.compile(r"\d{4}-\d{2}-\d{2}")

ASK = {
    "first_name": "your first name",
    "last_name": "your last name",
    "car_number": "your car number (for example TS09AB1234)",
    "start": "the start date and time (format YYYY-MM-DD HH:MM, 24 hour clock)",
    "end": "the end date and time (format YYYY-MM-DD HH:MM, 24 hour clock)",
}


def reply_problem(thread_id: str, reply: str) -> str | None:
    """Detect a reply that asks the customer to confirm a reservation that is
    incomplete or whose summary does not match the saved details."""
    text = reply.lower()
    if not (any(word in text for word in CONFIRM_WORDS) and DATE_IN_TEXT.search(reply)):
        return None

    draft = _drafts.get(thread_id, {})
    if not draft and thread_id in _sent:
        return None

    missing = missing_fields(draft)
    if missing:
        return (
            "Your last reply asked the customer to confirm a reservation, but these "
            f"details were never given: {', '.join(missing)}. Do not show a summary. "
            + next_prompt(draft)
        )
    if all(draft[key] in reply for key in ("car_number", "start", "end")):
        return None
    return "Your summary does not match the saved details. " + next_prompt(draft)


def safe_reply(thread_id: str) -> str:
    draft = _drafts.get(thread_id, {})
    missing = missing_fields(draft)
    if missing:
        return f"Before I can confirm anything, I still need {ASK[missing[0]]}."
    return (
        "Please confirm the reservation details:\n"
        f"Name: {draft['first_name']} {draft['last_name']}\n"
        f"Car number: {draft['car_number']}\n"
        f"From: {draft['start']}\n"
        f"To: {draft['end']}\n\n"
        "Shall I submit this request? (yes / no)"
    )