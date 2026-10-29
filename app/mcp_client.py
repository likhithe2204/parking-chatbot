import asyncio
import os

from dotenv import load_dotenv
from mcp import ClientSession
from mcp.client.streamable_http import streamablehttp_client

load_dotenv()


class RecorderError(Exception):
    pass


def _root_cause(exc: BaseException) -> BaseException:
    while isinstance(exc, BaseExceptionGroup) and exc.exceptions:
        exc = exc.exceptions[0]
    return exc


class ReservationRecorder:
    def __init__(self, url=None, api_key=None, timeout: float = 15.0):
        self.url = url or os.environ.get("MCP_SERVER_URL", "http://127.0.0.1:8001/mcp")
        self.api_key = api_key or os.environ.get("MCP_API_KEY", "")
        self.timeout = timeout

    async def _call(self, arguments: dict) -> str:
        headers = {"X-API-Key": self.api_key}
        async with streamablehttp_client(self.url, headers=headers) as (read, write, _):
            async with ClientSession(read, write) as session:
                await session.initialize()
                result = await session.call_tool("save_reservation", arguments)
        text = " ".join(
            block.text for block in result.content if getattr(block, "text", None)
        )
        if result.isError:
            raise RecorderError(text or "The MCP server rejected the reservation")
        return text

    def record(self, record: dict) -> str:
        arguments = {
            "first_name": record["first_name"],
            "last_name": record["last_name"],
            "car_number": record["car_number"],
            "start": record["start"],
            "end": record["end"],
            "approval_time": record["decided_at"],
        }
        try:
            return asyncio.run(asyncio.wait_for(self._call(arguments), self.timeout))
        except RecorderError:
            raise
        except BaseException as exc:
            if isinstance(exc, (KeyboardInterrupt, SystemExit)):
                raise
            cause = _root_cause(exc)
            raise RecorderError(
                f"Cannot reach the MCP server: {cause or type(cause).__name__}"
            ) from exc