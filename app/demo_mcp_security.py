from app.mcp_client import RecorderError, ReservationRecorder

SAMPLE = {
    "first_name": "Demo",
    "last_name": "Customer",
    "car_number": "TS11EF3333",
    "start": "2026-12-07 10:00",
    "end": "2026-12-07 14:00",
    "decided_at": "2026-10-29 09:00:00",
}

CASES = [
    ("Wrong API key", ReservationRecorder(api_key="wrong-key"), SAMPLE),
    ("Bad car number", ReservationRecorder(), {**SAMPLE, "car_number": "ABC"}),
    ("Separator in a name", ReservationRecorder(), {**SAMPLE, "first_name": "Bob | Evil"}),
    ("End before start", ReservationRecorder(), {**SAMPLE, "end": "2026-12-07 09:00"}),
]

for label, recorder, record in CASES:
    try:
        print(f"{label}: ACCEPTED - {recorder.record(record)}")
    except RecorderError as exc:
        print(f"{label}: BLOCKED - {exc}")