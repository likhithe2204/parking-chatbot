import threading

from app.workflow import create_workflow

SESSION = "session-1"
POLL_SECONDS = 3.0


def _watch(workflow, stop: threading.Event, interval: float) -> None:
    """Tell the customer as soon as the administrator decides."""
    while not stop.wait(interval):
        try:
            for _, text in workflow.poll():
                print(f"\n[Update] {text}\nYou: ", end="", flush=True)
        except Exception:
            pass  # poll() already logs problems; the watcher must never die


def main() -> None:
    workflow = create_workflow()

    try:
        saved = workflow.reconcile()
        if saved:
            print(f"Saved {saved} approved booking(s) that were waiting.")
    except Exception as exc:
        print(f"Note: could not check earlier bookings ({exc}).")

    stop = threading.Event()
    threading.Thread(
        target=_watch, args=(workflow, stop, POLL_SECONDS), daemon=True
    ).start()

    print("Hyderabad Central Parking assistant. Type 'exit' to quit.\n")
    try:
        while True:
            user_input = input("You: ").strip()
            if user_input.lower() in {"exit", "quit"}:
                break
            if not user_input:
                continue
            try:
                reply = workflow.send(SESSION, user_input)
            except Exception:
                reply = "Sorry, something went wrong on my side. Please try again."
            print(f"Bot: {reply}\n")
    finally:
        stop.set()


if __name__ == "__main__":
    main()