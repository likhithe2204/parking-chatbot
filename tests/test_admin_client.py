import json

import httpx
import pytest

from app.admin_client import AdminClient, AdminServiceError


def make_client(handler):
    return AdminClient(
        base_url="http://test", api_key="secret", transport=httpx.MockTransport(handler)
    )


def test_submit_request_sends_the_key_and_the_body():
    seen = {}

    def handler(request):
        seen["key"] = request.headers["x-api-key"]
        seen["path"] = request.url.path
        seen["body"] = json.loads(request.content)
        return httpx.Response(201, json={"id": "RES-AAAAAA", "status": "PENDING"})

    record = make_client(handler).submit_request(
        "Likhith", "Edupuganti", "TS09AB1234", "2099-01-01 10:00", "2099-01-01 12:00", "hi"
    )
    assert record["id"] == "RES-AAAAAA"
    assert seen["key"] == "secret"
    assert seen["path"] == "/requests"
    assert seen["body"]["car_number"] == "TS09AB1234"


def test_list_requests_passes_the_status_filter():
    seen = {}

    def handler(request):
        seen["status"] = request.url.params.get("status")
        return httpx.Response(200, json=[])

    assert make_client(handler).list_requests("PENDING") == []
    assert seen["status"] == "PENDING"


def test_decide_posts_the_decision():
    seen = {}

    def handler(request):
        seen["path"] = request.url.path
        seen["body"] = json.loads(request.content)
        return httpx.Response(200, json={"status": "APPROVED"})

    result = make_client(handler).decide("RES-AAAAAA", "APPROVED", "ok")
    assert result["status"] == "APPROVED"
    assert seen["path"] == "/requests/RES-AAAAAA/decision"
    assert seen["body"] == {"decision": "APPROVED", "reason": "ok"}


def test_http_error_becomes_a_readable_exception():
    def handler(request):
        return httpx.Response(409, json={"detail": "Request was already decided"})

    with pytest.raises(AdminServiceError) as error:
        make_client(handler).decide("RES-AAAAAA", "REFUSED")
    assert "already decided" in str(error.value)


def test_unreachable_service_becomes_a_readable_exception():
    def handler(request):
        raise httpx.ConnectError("boom")

    with pytest.raises(AdminServiceError) as error:
        make_client(handler).list_requests()
    assert "Cannot reach" in str(error.value)

def test_error_carries_the_status_code():
    def handler(request):
        return httpx.Response(404, json={"detail": "Request not found"})

    with pytest.raises(AdminServiceError) as error:
        make_client(handler).get_request("RES-NOPE00")
    assert error.value.status_code == 404