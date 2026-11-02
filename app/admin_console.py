import argparse
from app.admin_client import AdminClient, AdminServiceError
from app.mcp_client import RecorderError, ReservationRecorder


def format_request(record: dict) -> str:
    lines = [
        f"Request:    {record['id']}",
        f"Customer:   {record['first_name']} {record['last_name']}",
        f"Car number: {record['car_number']}",
        f"Period:     {record['start']} -> {record['end']}",
        f"Status:     {record['status']}",
    ]
    if record.get("note"):
        lines.append(f"Note:       {record['note']}")
    return "\n".join(lines)


def _save(recorder, record: dict, output_fn) -> bool:
    try:
        result = recorder.record(record)
    except RecorderError as exc:
        output_fn(f"Warning: approved, but the booking was not saved: {exc}")
        output_fn("Start the MCP server, then type s at the next prompt to save it.")
        return False
    output_fn(f"MCP server: {result}")
    return True


def _sync(client, recorder, output_fn) -> None:
    if recorder is None:
        output_fn("No MCP server is configured.")
        return
    try:
        approved = client.list_requests("APPROVED")
    except AdminServiceError as exc:
        output_fn(f"Error: {exc}")
        return
    if not approved:
        output_fn("No approved bookings to save.")
        return
    for record in approved:
        _save(recorder, record, output_fn)


def _review(client, request_id: str, input_fn, output_fn, recorder=None) -> None:
    try:
        record = client.get_request(request_id)
    except AdminServiceError as exc:
        output_fn(f"Error: {exc}")
        return

    output_fn("\n" + format_request(record))
    if record["status"] != "PENDING":
        output_fn(f"Already {record['status']}.")
        return

    answer = input_fn("approve / refuse / skip: ").strip().lower()
    if answer not in {"approve", "refuse"}:
        output_fn("Skipped.")
        return

    decision = "APPROVED" if answer == "approve" else "REFUSED"
    reason = input_fn("Reason (optional): ").strip()
    try:
        decided = client.decide(record["id"], decision, reason)
    except AdminServiceError as exc:
        output_fn(f"Error: {exc}")
        return
    output_fn(f"{record['id']} marked {decision}.")

    if decision == "APPROVED":
        if recorder is not None:
            _save(recorder, decided, output_fn)
        else:
            output_fn("The workflow saves the booking and tells the customer.")


def run(client, input_fn=input, output_fn=print, recorder=None) -> None:
    output_fn("Parking administrator console")
    while True:
        try:
            pending = client.list_requests("PENDING")
        except AdminServiceError as exc:
            output_fn(f"Error: {exc}")
            return

        if not pending:
            output_fn("\nNo pending requests.")
        else:
            output_fn(f"\n{len(pending)} pending request(s):")
            for record in pending:
                output_fn(
                    f"  {record['id']}  {record['first_name']} {record['last_name']}  "
                    f"{record['car_number']}  {record['start']} -> {record['end']}"
                )

        options = "Request id to review, "
        if recorder is not None:
            options += "s to save approved bookings, "
        choice = input_fn(f"\n{options}Enter to refresh, q to quit: ").strip()

        if choice.lower() == "q":
            return
        if choice.lower() == "s":
            _sync(client, recorder, output_fn)
        elif choice:
            _review(client, choice, input_fn, output_fn, recorder)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--save",
        action="store_true",
        help="also save approvals through the MCP server (stand-alone use, as in Stage 3)",
    )
    args = parser.parse_args()

    client = AdminClient()
    try:
        run(client, recorder=ReservationRecorder() if args.save else None)
    finally:
        client.close()


if __name__ == "__main__":
    main()