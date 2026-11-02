import argparse
import secrets
import socket
import tempfile
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from contextlib import contextmanager
from datetime import datetime
from pathlib import Path

import uvicorn

from app.admin_api import create_app as create_admin_app
from app.admin_client import AdminClient
from app.config import ROOT
from app.evaluation import summarize_latency
from app.mcp_client import ReservationRecorder
from app.mcp_server import create_app as create_mcp_app

REPORT_PATH = ROOT / "docs" / "load_test_report.md"

ADMIN = "Administrator confirmation (create and approve)"
MCP = "MCP server recording"
CHATBOT = "Chatbot dialogue"

QUESTIONS = [
    "Where is the parking located?",
    "How much does it cost for a car?",
    "Are there free spaces in Zone C?",
]


def plate(index: int) -> str:
    return f"TS{10 + index % 90:02d}AB{1000 + index:04d}"


def _free_port() -> int:
    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        return sock.getsockname()[1]


@contextmanager
def running_server(app):
    """Run a FastAPI app on a free local port for the duration of a test."""
    port = _free_port()
    server = uvicorn.Server(
        uvicorn.Config(app, host="127.0.0.1", port=port, log_level="warning")
    )
    thread = threading.Thread(target=server.run, daemon=True)
    thread.start()

    deadline = time.time() + 15
    while not server.started:
        if time.time() > deadline:
            server.should_exit = True
            raise RuntimeError("The test server did not start")
        time.sleep(0.05)
    try:
        yield f"http://127.0.0.1:{port}"
    finally:
        server.should_exit = True
        thread.join(timeout=10)


def _run(task, count: int, workers: int) -> dict:
    def timed(index: int):
        start = time.perf_counter()
        try:
            task(index)
            ok = True
        except Exception:
            ok = False
        return (time.perf_counter() - start) * 1000, ok

    begin = time.perf_counter()
    with ThreadPoolExecutor(max_workers=workers) as pool:
        results = list(pool.map(timed, range(count)))
    elapsed = time.perf_counter() - begin

    return {
        "operations": count,
        "workers": workers,
        "errors": sum(1 for _, ok in results if not ok),
        "throughput": round(count / elapsed, 1) if elapsed else 0.0,
        "latency": summarize_latency([ms for ms, ok in results if ok]),
    }


def run_admin_load(count: int = 50, workers: int = 10) -> dict:
    key = secrets.token_urlsafe(16)
    with tempfile.TemporaryDirectory() as folder:
        app = create_admin_app(db_path=Path(folder) / "admin.db", api_key=key)
        with running_server(app) as base_url:

            def confirm(index: int) -> None:
                client = AdminClient(base_url=base_url, api_key=key)
                try:
                    record = client.submit_request(
                        "Load", "Tester", plate(index),
                        "2099-01-01 10:00", "2099-01-01 12:00", "load test",
                    )
                    client.decide(record["id"], "APPROVED", "load test")
                finally:
                    client.close()

            result = _run(confirm, count, workers)

            checker = AdminClient(base_url=base_url, api_key=key)
            try:
                approved = len(checker.list_requests("APPROVED"))
            finally:
                checker.close()

    expected = count - result["errors"]
    result["checks"] = {"approved requests stored": f"{approved} of {expected}"}
    result["consistent"] = approved == expected
    return result


def run_mcp_load(count: int = 50, workers: int = 10) -> dict:
    key = secrets.token_urlsafe(16)

    def booking(index: int) -> dict:
        return {
            "first_name": "Load",
            "last_name": "Tester",
            "car_number": plate(index),
            "start": "2099-01-01 10:00",
            "end": "2099-01-01 12:00",
            "decided_at": "2026-10-29 10:00:00",
        }

    with tempfile.TemporaryDirectory() as folder:
        file_path = Path(folder) / "reservations.txt"
        with running_server(create_mcp_app(path=file_path, api_key=key)) as base_url:
            recorder = ReservationRecorder(url=f"{base_url}/mcp", api_key=key)

            result = _run(lambda index: recorder.record(booking(index)), count, workers)

            replay = min(count - result["errors"], 10)
            ignored = 0
            for index in range(replay):
                try:
                    if recorder.record(booking(index)).startswith("ALREADY_RECORDED"):
                        ignored += 1
                except Exception:
                    pass

        lines = file_path.read_text(encoding="utf-8").splitlines() if file_path.exists() else []

    expected = count - result["errors"]
    well_formed = all(len(line.split(" | ")) == 4 for line in lines)
    result["checks"] = {
        "lines written": f"{len(lines)} of {expected}",
        "unique lines": f"{len(set(lines))} of {len(lines)}",
        "well formed (4 columns)": "yes" if well_formed else "NO",
        "repeated bookings ignored": f"{ignored} of {replay}",
    }
    result["consistent"] = (
        len(lines) == expected and len(set(lines)) == len(lines)
        and well_formed and ignored == replay
    )
    return result


def run_chatbot_load(sessions: int = 3, messages: int = 3) -> dict:
    from app.workflow import create_workflow  # real model: needs the VPN

    workflow = create_workflow()
    workflow.send("warm-up", "Hello")

    def one_session(number: int) -> list[tuple[float, bool]]:
        outcomes = []
        for turn in range(messages):
            question = QUESTIONS[turn % len(QUESTIONS)]
            start = time.perf_counter()
            try:
                reply = workflow.send(f"load-{number}", question)
                ok = bool(reply.strip())
            except Exception:
                ok = False
            outcomes.append(((time.perf_counter() - start) * 1000, ok))
        return outcomes

    begin = time.perf_counter()
    with ThreadPoolExecutor(max_workers=sessions) as pool:
        outcomes = [item for batch in pool.map(one_session, range(sessions)) for item in batch]
    elapsed = time.perf_counter() - begin

    total = sessions * messages
    return {
        "operations": total,
        "workers": sessions,
        "errors": sum(1 for _, ok in outcomes if not ok),
        "throughput": round(total / elapsed, 2) if elapsed else 0.0,
        "latency": summarize_latency([ms for ms, ok in outcomes if ok]),
        "checks": {"concurrent conversations": str(sessions)},
        "consistent": True,
    }


def render_report(results: dict) -> str:
    lines = [
        "# Load Test Report",
        "",
        f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}",
        "",
        "Each run starts its own servers on free local ports with temporary storage,",
        "so the real data is never touched.",
        "",
        "## Results",
        "",
        "| Component | Operations | Concurrency | Errors | Throughput (ops/s) | Mean ms | p50 ms | p95 ms | Max ms |",
        "|---|---|---|---|---|---|---|---|---|",
    ]
    for name, result in results.items():
        latency = result["latency"]
        lines.append(
            f"| {name} | {result['operations']} | {result['workers']} | {result['errors']} "
            f"| {result['throughput']} | {latency['mean']} | {latency['p50']} "
            f"| {latency['p95']} | {latency['max']} |"
        )

    lines += ["", "## Integrity checks", ""]
    for name, result in results.items():
        for label, value in result.get("checks", {}).items():
            lines.append(f"- {name}: {label}: {value}")
        verdict = "consistent" if result.get("consistent") else "INCONSISTENT"
        lines.append(f"- {name}: result {verdict}")
    lines.append("")
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--count", type=int, default=50, help="operations per server test")
    parser.add_argument("--workers", type=int, default=10, help="concurrent workers")
    parser.add_argument("--sessions", type=int, default=3, help="chatbot conversations")
    parser.add_argument("--messages", type=int, default=3, help="messages per conversation")
    parser.add_argument("--skip-chatbot", action="store_true", help="skip the LLM based test")
    args = parser.parse_args()

    results = {}
    print("Load testing the administrator confirmation...")
    results[ADMIN] = run_admin_load(args.count, args.workers)
    print("Load testing the MCP server recording...")
    results[MCP] = run_mcp_load(args.count, args.workers)
    if not args.skip_chatbot:
        print("Load testing the chatbot dialogue (needs the VPN)...")
        results[CHATBOT] = run_chatbot_load(args.sessions, args.messages)

    report = render_report(results)
    REPORT_PATH.parent.mkdir(exist_ok=True)
    REPORT_PATH.write_text(report, encoding="utf-8")
    print("\n" + report)
    print(f"Report saved to {REPORT_PATH}")


if __name__ == "__main__":
    main()