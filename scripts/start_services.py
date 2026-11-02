"""Start the admin service and the MCP server together. Press Ctrl+C to stop both."""

import socket
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

SERVICES = [
    ("admin service", "app.admin_api:create_app", 8000),
    ("MCP server", "app.mcp_server:create_app", 8001),
]


def port_in_use(port: int) -> bool:
    with socket.socket() as sock:
        sock.settimeout(1)
        return sock.connect_ex(("127.0.0.1", port)) == 0


def check_ports() -> None:
    busy = [(name, port) for name, _, port in SERVICES if port_in_use(port)]
    if not busy:
        return

    for name, port in busy:
        print(f"Port {port} ({name}) is already in use, most likely by an older server.")
    ports = ",".join(str(port) for _, _, port in SERVICES)
    print("\nSee what is using the ports (PowerShell):")
    print(f"  Get-NetTCPConnection -LocalPort {ports} -State Listen | Select-Object LocalPort, OwningProcess")
    print("Stop those servers, then run this script again:")
    print(
        f"  Get-NetTCPConnection -LocalPort {ports} -State Listen | "
        "ForEach-Object { Stop-Process -Id $_.OwningProcess -Force }"
    )
    sys.exit(1)


def main() -> None:
    check_ports()

    processes = []
    try:
        for name, target, port in SERVICES:
            command = [
                sys.executable, "-m", "uvicorn", target,
                "--factory", "--host", "127.0.0.1", "--port", str(port),
            ]
            processes.append(subprocess.Popen(command, cwd=ROOT))
            print(f"Started {name} on http://127.0.0.1:{port}")

        while all(process.poll() is None for process in processes):
            time.sleep(1)
        print("A service stopped, shutting both down.")
    except KeyboardInterrupt:
        print("\nStopping the services...")
    finally:
        for process in processes:
            if process.poll() is None:
                process.terminate()
        for process in processes:
            try:
                process.wait(timeout=10)
            except subprocess.TimeoutExpired:
                process.kill()


if __name__ == "__main__":
    main()