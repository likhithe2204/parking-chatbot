import sqlite3
import uuid
from datetime import datetime
from pathlib import Path

from app.config import ADMIN_DB_PATH

STATUSES = ("PENDING", "APPROVED", "REFUSED")
DECISIONS = ("APPROVED", "REFUSED")

SCHEMA = """
CREATE TABLE IF NOT EXISTS reservation_requests (
    id TEXT PRIMARY KEY,
    first_name TEXT NOT NULL,
    last_name TEXT NOT NULL,
    car_number TEXT NOT NULL,
    period_start TEXT NOT NULL,
    period_end TEXT NOT NULL,
    note TEXT NOT NULL DEFAULT '',
    status TEXT NOT NULL DEFAULT 'PENDING',
    reason TEXT NOT NULL DEFAULT '',
    created_at TEXT NOT NULL,
    decided_at TEXT
);
"""


class RequestNotFound(Exception):
    pass


class AlreadyDecided(Exception):
    pass


def _now() -> str:
    return datetime.now().isoformat(timespec="seconds")


def _connect(db_path) -> sqlite3.Connection:
    path = Path(db_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    conn.executescript(SCHEMA)
    return conn


def _to_dict(row: sqlite3.Row) -> dict:
    data = dict(row)
    data["start"] = data.pop("period_start")
    data["end"] = data.pop("period_end")
    return data


def create_request(
    first_name: str,
    last_name: str,
    car_number: str,
    start: str,
    end: str,
    note: str = "",
    db_path=ADMIN_DB_PATH,
) -> dict:
    request_id = f"RES-{uuid.uuid4().hex[:6].upper()}"
    conn = _connect(db_path)
    try:
        conn.execute(
            "INSERT INTO reservation_requests "
            "(id, first_name, last_name, car_number, period_start, period_end, "
            "note, created_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            (request_id, first_name, last_name, car_number, start, end, note[:1000], _now()),
        )
        conn.commit()
    finally:
        conn.close()
    return get_request(request_id, db_path)


def get_request(request_id: str, db_path=ADMIN_DB_PATH) -> dict | None:
    conn = _connect(db_path)
    try:
        row = conn.execute(
            "SELECT * FROM reservation_requests WHERE id = ?",
            (request_id.strip().upper(),),
        ).fetchone()
    finally:
        conn.close()
    return _to_dict(row) if row else None


def list_requests(status: str | None = None, db_path=ADMIN_DB_PATH) -> list[dict]:
    if status is not None and status not in STATUSES:
        raise ValueError(f"Unknown status '{status}'")
    sql = "SELECT * FROM reservation_requests"
    params: tuple = ()
    if status:
        sql += " WHERE status = ?"
        params = (status,)
    sql += " ORDER BY created_at, id"

    conn = _connect(db_path)
    try:
        rows = conn.execute(sql, params).fetchall()
    finally:
        conn.close()
    return [_to_dict(row) for row in rows]


def decide(
    request_id: str, decision: str, reason: str = "", db_path=ADMIN_DB_PATH
) -> dict:
    if decision not in DECISIONS:
        raise ValueError(f"Decision must be one of {DECISIONS}")
    rid = request_id.strip().upper()

    conn = _connect(db_path)
    try:
        cursor = conn.execute(
            "UPDATE reservation_requests SET status = ?, reason = ?, decided_at = ? "
            "WHERE id = ? AND status = 'PENDING'",
            (decision, reason[:500], _now(), rid),
        )
        conn.commit()
        changed = cursor.rowcount
    finally:
        conn.close()

    if changed == 0:
        if get_request(rid, db_path) is None:
            raise RequestNotFound(rid)
        raise AlreadyDecided(rid)
    return get_request(rid, db_path)