from app import admin_console
from app.admin_client import AdminServiceError
from app.mcp_client import RecorderError

PENDING = {
    "id": "RES-AAAAAA",
    "first_name": "Likhith",
    "last_name": "Edupuganti",
    "car_number": "TS09AB1234",
    "start": "2099-01-01 10:00",
    "end": "2099-01-01 12:00",
    "note": "Zone B has space",
    "status": "PENDING",
}


class FakeClient:
    def __init__(self, records):
        self.records = {r["id"]: dict(r) for r in records}
        self.decided = []

    def list_requests(self, status=None):
        return [r for r in self.records.values() if status is None or r["status"] == status]

    def get_request(self, request_id):
        return self.records[request_id]

    def decide(self, request_id, decision, reason=""):
        self.decided.append((request_id, decision, reason))
        self.records[request_id]["status"] = decision
        return self.records[request_id]


class BrokenClient:
    def list_requests(self, status=None):
        raise AdminServiceError("down")


def run_console(client, answers, recorder=None):
    outputs = []
    feed = iter(answers)
    admin_console.run(
        client,
        input_fn=lambda _="": next(feed),
        output_fn=outputs.append,
        recorder=recorder,
    )
    return "\n".join(outputs)


def test_format_request_shows_the_details():
    text = admin_console.format_request(PENDING)
    assert "RES-AAAAAA" in text
    assert "TS09AB1234" in text
    assert "Zone B has space" in text


def test_administrator_can_approve():
    client = FakeClient([PENDING])
    output = run_console(client, ["RES-AAAAAA", "approve", "all good", "q"])
    assert client.decided == [("RES-AAAAAA", "APPROVED", "all good")]
    assert "marked APPROVED" in output


def test_administrator_can_refuse_with_a_reason():
    client = FakeClient([PENDING])
    run_console(client, ["RES-AAAAAA", "refuse", "zone full", "q"])
    assert client.decided == [("RES-AAAAAA", "REFUSED", "zone full")]


def test_skip_does_not_decide():
    client = FakeClient([PENDING])
    output = run_console(client, ["RES-AAAAAA", "skip", "q"])
    assert client.decided == []
    assert "Skipped" in output


def test_empty_queue_is_reported():
    output = run_console(FakeClient([]), ["q"])
    assert "No pending requests" in output


def test_service_error_stops_the_console():
    output = run_console(BrokenClient(), [])
    assert "Error: down" in output

class FakeRecorder:
    def __init__(self, error=None):
        self.error = error
        self.recorded = []

    def record(self, record):
        if self.error:
            raise self.error
        self.recorded.append(record["id"])
        return f"SAVED: {record['id']}"


def test_approval_saves_the_booking_through_the_mcp_server():
    client = FakeClient([PENDING])
    recorder = FakeRecorder()
    output = run_console(client, ["RES-AAAAAA", "approve", "ok", "q"], recorder)
    assert recorder.recorded == ["RES-AAAAAA"]
    assert "SAVED: RES-AAAAAA" in output


def test_refusal_does_not_save_anything():
    client = FakeClient([PENDING])
    recorder = FakeRecorder()
    run_console(client, ["RES-AAAAAA", "refuse", "zone full", "q"], recorder)
    assert recorder.recorded == []


def test_failed_save_is_reported_and_the_decision_is_kept():
    client = FakeClient([PENDING])
    recorder = FakeRecorder(error=RecorderError("down"))
    output = run_console(client, ["RES-AAAAAA", "approve", "ok", "q"], recorder)
    assert "not saved" in output
    assert client.decided == [("RES-AAAAAA", "APPROVED", "ok")]


def test_s_saves_every_approved_booking():
    client = FakeClient([{**PENDING, "status": "APPROVED"}])
    recorder = FakeRecorder()
    run_console(client, ["s", "q"], recorder)
    assert recorder.recorded == ["RES-AAAAAA"]