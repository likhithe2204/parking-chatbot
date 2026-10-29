import asyncio

import pytest

from app.mcp_client import RecorderError, ReservationRecorder

RECORD = {
    "id": "RES-AAAAAA",
    "first_name": "Likhith",
    "last_name": "Edupuganti",
    "car_number": "TS09AB1234",
    "start": "2026-12-05 10:00",
    "end": "2026-12-05 14:00",
    "status": "APPROVED",
    "decided_at": "2026-10-28T17:34:59",
}


def recorder(timeout=5.0):
    return ReservationRecorder(url="http://127.0.0.1:1/mcp", api_key="k", timeout=timeout)


def fake_call(monkeypatch, behavior):
    async def _call(self, arguments):
        return await behavior(arguments)

    monkeypatch.setattr(ReservationRecorder, "_call", _call)


def test_record_sends_the_reservation_with_the_approval_time(monkeypatch):
    seen = {}

    async def behavior(arguments):
        seen.update(arguments)
        return "SAVED: line"

    fake_call(monkeypatch, behavior)
    assert recorder().record(RECORD) == "SAVED: line"
    assert seen == {
        "first_name": "Likhith",
        "last_name": "Edupuganti",
        "car_number": "TS09AB1234",
        "start": "2026-12-05 10:00",
        "end": "2026-12-05 14:00",
        "approval_time": "2026-10-28T17:34:59",
    }


def test_server_rejection_is_passed_on(monkeypatch):
    async def behavior(arguments):
        raise RecorderError("Rejected: Car number must look like TS09AB1234")

    fake_call(monkeypatch, behavior)
    with pytest.raises(RecorderError) as error:
        recorder().record(RECORD)
    assert "Rejected" in str(error.value)


def test_unreachable_server_becomes_a_readable_error(monkeypatch):
    async def behavior(arguments):
        raise ConnectionError("boom")

    fake_call(monkeypatch, behavior)
    with pytest.raises(RecorderError) as error:
        recorder().record(RECORD)
    assert "Cannot reach" in str(error.value)
    assert "boom" in str(error.value)


def test_exception_groups_are_unwrapped(monkeypatch):
    async def behavior(arguments):
        raise ExceptionGroup("unhandled errors in a TaskGroup", [ConnectionError("boom")])

    fake_call(monkeypatch, behavior)
    with pytest.raises(RecorderError) as error:
        recorder().record(RECORD)
    assert "boom" in str(error.value)
    assert "TaskGroup" not in str(error.value)


def test_a_slow_server_times_out(monkeypatch):
    async def behavior(arguments):
        await asyncio.sleep(5)

    fake_call(monkeypatch, behavior)
    with pytest.raises(RecorderError) as error:
        recorder(timeout=0.05).record(RECORD)
    assert "Cannot reach" in str(error.value)