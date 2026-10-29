import hmac
import json
import os
from contextlib import asynccontextmanager
from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI
from mcp.server.fastmcp import FastMCP

from app.config import RESERVATIONS_FILE
from app.reservation_file import InvalidReservation, append_reservation

load_dotenv()


class ApiKeyMiddleware:
    """Pure ASGI middleware: every request needs the key, except the health check."""

    def __init__(self, app, api_key: str, open_paths: tuple = ("/health",)):
        self.app = app
        self.api_key = api_key.encode()
        self.open_paths = open_paths

    async def __call__(self, scope, receive, send):
        if scope["type"] == "http" and scope["path"] not in self.open_paths:
            supplied = dict(scope["headers"]).get(b"x-api-key", b"")
            if not hmac.compare_digest(supplied, self.api_key):
                body = json.dumps({"detail": "Invalid or missing API key"}).encode()
                await send(
                    {
                        "type": "http.response.start",
                        "status": 401,
                        "headers": [
                            (b"content-type", b"application/json"),
                            (b"content-length", str(len(body)).encode()),
                        ],
                    }
                )
                await send({"type": "http.response.body", "body": body})
                return
        await self.app(scope, receive, send)


def create_mcp(file_path: Path) -> FastMCP:
    mcp = FastMCP("Parking Reservations", stateless_http=True, json_response=True)

    @mcp.tool()
    def save_reservation(
        first_name: str,
        last_name: str,
        car_number: str,
        start: str,
        end: str,
        approval_time: str,
    ) -> str:
        """Write one administrator-approved reservation to the reservations file.
        start and end use the format YYYY-MM-DD HH:MM. approval_time is the moment
        the administrator approved, for example 2026-12-05 09:30:00."""
        try:
            line, created = append_reservation(
                first_name, last_name, car_number, start, end, approval_time, file_path
            )
        except InvalidReservation as exc:
            raise ValueError(f"Rejected: {exc}") from exc
        return ("SAVED: " if created else "ALREADY_RECORDED: ") + line

    return mcp


def create_app(path=None, api_key: str | None = None) -> FastAPI:
    key = api_key or os.environ.get("MCP_API_KEY", "")
    if not key:
        raise RuntimeError("MCP_API_KEY is not set")

    mcp = create_mcp(Path(path) if path else RESERVATIONS_FILE)
    mcp_app = mcp.streamable_http_app()

    @asynccontextmanager
    async def lifespan(_app):
        async with mcp.session_manager.run():
            yield

    api = FastAPI(title="Parking MCP Server", lifespan=lifespan)

    @api.get("/health")
    def health() -> dict:
        return {"status": "ok"}

    api.mount("/", mcp_app)
    api.add_middleware(ApiKeyMiddleware, api_key=key)
    return api