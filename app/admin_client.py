import os

import httpx
from dotenv import load_dotenv

load_dotenv()


class AdminServiceError(Exception):
    pass


def _detail(response: httpx.Response) -> str:
    try:
        return str(response.json()["detail"])
    except (ValueError, KeyError, TypeError):
        return response.text[:200]


class AdminClient:
    def __init__(self, base_url=None, api_key=None, transport=None, timeout=10.0):
        self._client = httpx.Client(
            base_url=base_url or os.environ.get("ADMIN_API_URL", "http://127.0.0.1:8000"),
            headers={"X-API-Key": api_key or os.environ.get("ADMIN_API_KEY", "")},
            transport=transport,
            timeout=timeout,
        )

    def _send(self, method: str, url: str, **kwargs):
        try:
            response = self._client.request(method, url, **kwargs)
        except httpx.HTTPError as exc:
            raise AdminServiceError(f"Cannot reach the admin service: {exc}") from exc
        if response.status_code >= 400:
            raise AdminServiceError(
                f"Admin service error {response.status_code}: {_detail(response)}"
            )
        return response.json()

    def submit_request(
        self,
        first_name: str,
        last_name: str,
        car_number: str,
        start: str,
        end: str,
        note: str = "",
    ) -> dict:
        body = {
            "first_name": first_name,
            "last_name": last_name,
            "car_number": car_number,
            "start": start,
            "end": end,
            "note": note,
        }
        return self._send("POST", "/requests", json=body)

    def get_request(self, request_id: str) -> dict:
        return self._send("GET", f"/requests/{request_id}")

    def list_requests(self, status: str | None = None) -> list[dict]:
        params = {"status": status} if status else None
        return self._send("GET", "/requests", params=params)

    def decide(self, request_id: str, decision: str, reason: str = "") -> dict:
        body = {"decision": decision, "reason": reason}
        return self._send("POST", f"/requests/{request_id}/decision", json=body)

    def close(self) -> None:
        self._client.close()