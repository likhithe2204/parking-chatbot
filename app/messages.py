RECORDING_NOTES = {
    "RECORDED": " Your booking is now saved.",
    "ALREADY_RECORDED": " Your booking is saved.",
    "RECORD_FAILED": " The booking could not be saved yet. Please ask again in a moment.",
    "NO_SPACE": (
        " However, no space is free for that period any more, so the booking was not "
        "saved. Please contact the parking office."
    ),
}


def decision_message(record: dict) -> str:
    request_id = record["id"]
    status = record["status"]
    if status == "PENDING":
        return f"Request {request_id} is still waiting for the administrator's decision."

    if status == "APPROVED":
        text = f"Good news: the administrator approved request {request_id}."
    else:
        text = f"Sorry, the administrator refused request {request_id}."
    if record.get("reason"):
        text += f" Reason: {record['reason']}"
    return text


def status_message(record: dict, recording: str) -> str:
    return decision_message(record) + RECORDING_NOTES.get(recording, "")