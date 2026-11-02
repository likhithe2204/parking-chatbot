import logging
import sqlite3
from dataclasses import dataclass

from langchain.agents import create_agent
from langchain_core.tools import tool

from app.admin_client import AdminClient, AdminServiceError
from app.bookings import NoSpaceAvailable
from app.llm import get_llm
from app.mcp_client import RecorderError, ReservationRecorder
from app.messages import RECORDING_NOTES, decision_message, status_message  
from app.tools import format_availability

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """You prepare reservation requests for the human administrator
of Hyderabad Central Parking.

You receive the customer's reservation details. Do this:
1. Call check_availability once to see how many spaces are free.
2. Write a short note for the administrator, at most 3 sentences: who the
   customer is, the car, the period, and what the availability looks like.
3. Call send_to_administrator once with that note.
4. After the tool confirms, reply with the single word DONE.

Rules:
- Never invent details and never change the customer's details. They are
  attached to the request automatically.
- Do not approve or refuse the request. The administrator decides."""


@dataclass(frozen=True)
class Escalation:
    request_id: str
    note: str
    record: dict


def default_note(first_name: str, last_name: str, car_number: str, start: str, end: str) -> str:
    return (
        f"Customer {first_name} {last_name} requests a parking space "
        f"for car {car_number} from {start} to {end}."
    )


class AdminAgent:
    def __init__(self, client=None, llm=None, recorder=None, allocator=None):
        self.client = client or AdminClient()
        self._llm = llm
        self.recorder = recorder or ReservationRecorder()
        self.allocator = allocator

    def escalate(
        self, first_name: str, last_name: str, car_number: str, start: str, end: str
    ) -> Escalation:
        sent: dict = {}


        @tool
        def check_availability(zone: str = "") -> str:
            """Get the number of free parking spaces for the customer's requested
            period. Pass 'Zone A', 'Zone B' or 'Zone C', or leave empty to get all zones."""
            try:
                return format_availability(zone, start, end)
            except sqlite3.Error:
                return "Availability data is not available right now."

        @tool
        def send_to_administrator(note: str) -> str:
            """Send the reservation request to the human administrator together
            with a short note."""
            if sent:
                return f"Already sent as request {sent['id']}."
            try:
                record = self.client.submit_request(
                    first_name, last_name, car_number, start, end, note
                )
            except AdminServiceError as exc:
                return f"FAILED: {exc}"
            sent.update(record)
            return (
                f"Sent to the administrator as request {record['id']}. "
                f"Status: {record['status']}."
            )

        request = (
            "Reservation details:\n"
            f"- Customer: {first_name} {last_name}\n"
            f"- Car number: {car_number}\n"
            f"- Period: {start} to {end}"
        )
        try:
            agent = create_agent(
                model=self._llm or get_llm(),
                tools=[check_availability, send_to_administrator],
                system_prompt=SYSTEM_PROMPT,
            )
            agent.invoke({"messages": [{"role": "user", "content": request}]})
        except Exception as exc:
            # The note is a convenience. The request must reach the administrator
            # even when the model is unavailable.
            logger.warning("Note generation failed, using the default note: %s", exc)

        if not sent:
            record = self.client.submit_request(
                first_name,
                last_name,
                car_number,
                start,
                end,
                default_note(first_name, last_name, car_number, start, end),
            )
            sent.update(record)

        return Escalation(sent["id"], sent.get("note", ""), dict(sent))

    def get_decision(self, request_id: str) -> dict:
        return self.client.get_request(request_id)


    def settle(self, request_id: str) -> tuple[dict, str]:
        """Read the decision. If the request is approved, take a space for it and make
        sure the booking is saved through the MCP server. Safe to call repeatedly."""
        record = self.client.get_request(request_id)
        if record["status"] != "APPROVED":
            return record, "NOT_APPROVED"

        if self.allocator is not None:
            try:
                self.allocator(record)
            except NoSpaceAvailable as exc:
                logger.warning("Approved booking %s has no space: %s", request_id, exc)
                return record, "NO_SPACE"
            except sqlite3.Error as exc:
                logger.warning("Could not reserve a space for %s: %s", request_id, exc)
                return record, "RECORD_FAILED"

        try:
            result = self.recorder.record(record)
        except RecorderError as exc:
            logger.warning("Approved booking %s was not saved: %s", request_id, exc)
            return record, "RECORD_FAILED"
        if result.startswith("ALREADY_RECORDED"):
            return record, "ALREADY_RECORDED"
        return record, "RECORDED"