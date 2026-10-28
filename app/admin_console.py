from app.admin_client import AdminClient, AdminServiceError


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


def _review(client, request_id: str, input_fn, output_fn) -> None:
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
        client.decide(record["id"], decision, reason)
    except AdminServiceError as exc:
        output_fn(f"Error: {exc}")
        return
    output_fn(f"{record['id']} marked {decision}.")


def run(client, input_fn=input, output_fn=print) -> None:
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

        choice = input_fn("\nRequest id to review, Enter to refresh, q to quit: ").strip()
        if choice.lower() == "q":
            return
        if choice:
            _review(client, choice, input_fn, output_fn)


def main() -> None:
    client = AdminClient()
    try:
        run(client)
    finally:
        client.close()


if __name__ == "__main__":
    main()