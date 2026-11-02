import sqlite3
from datetime import datetime, timedelta
from pathlib import Path

from app.reservation import DATETIME_FORMAT
from app.seed_db import DB_PATH

SCHEMA = """
CREATE TABLE IF NOT EXISTS bookings (
    request_id TEXT PRIMARY KEY,
    zone TEXT NOT NULL,
    car_number TEXT NOT NULL,
    period_start TEXT NOT NULL,
    period_end TEXT NOT NULL
)
"""

FREE_SQL = """
SELECT a.zone AS zone,
       a.total_spaces AS total_spaces,
       MAX(a.available_spaces - COUNT(b.request_id), 0) AS free_spaces
FROM availability a
LEFT JOIN bookings b
       ON b.zone = a.zone AND b.period_start < :end AND b.period_end > :start
{where}
GROUP BY a.zone, a.total_spaces, a.available_spaces
ORDER BY a.zone
"""

BASELINE_SQL = """
SELECT zone, total_spaces, available_spaces AS free_spaces
FROM availability
{where}
ORDER BY zone
"""


class NoSpaceAvailable(Exception):
    pass


def window_for_now(now: datetime | None = None) -> tuple[str, str]:
    """A one minute window starting now, used to ask 'what is free right now'."""
    now = now or datetime.now()
    return now.strftime(DATETIME_FORMAT), (now + timedelta(minutes=1)).strftime(DATETIME_FORMAT)


def free_by_zone(start: str, end: str, zone: str | None = None, db_path=DB_PATH) -> list[dict]:
    """Free spaces per zone for a period: the zone's free spaces minus the approved
    bookings that overlap the period."""
    conn = sqlite3.connect(f"{Path(db_path).as_uri()}?mode=ro", uri=True)
    conn.row_factory = sqlite3.Row
    try:
        has_bookings = conn.execute(
            "SELECT 1 FROM sqlite_master WHERE type = 'table' AND name = 'bookings'"
        ).fetchone()
        where = "WHERE a.zone = :zone" if zone else ""
        params = {"start": start, "end": end}
        if zone:
            params["zone"] = zone.strip().title()

        if has_bookings:
            rows = conn.execute(FREE_SQL.format(where=where), params).fetchall()
        else:
            plain = "WHERE zone = :zone" if zone else ""
            plain_params = {"zone": params["zone"]} if zone else {}
            rows = conn.execute(BASELINE_SQL.format(where=plain), plain_params).fetchall()
    finally:
        conn.close()
    return [dict(row) for row in rows]


def allocate(request_id: str, car_number: str, start: str, end: str, db_path=DB_PATH):
    """Reserve one space for an approved booking. Returns (zone, created).
    Repeating the call for the same request id changes nothing."""
    request_id = request_id.strip().upper()
    conn = sqlite3.connect(db_path, isolation_level=None, timeout=10)
    conn.row_factory = sqlite3.Row
    try:
        conn.execute(SCHEMA)
        conn.execute("BEGIN IMMEDIATE")
        try:
            existing = conn.execute(
                "SELECT zone FROM bookings WHERE request_id = ?", (request_id,)
            ).fetchone()
            if existing:
                conn.execute("COMMIT")
                return existing["zone"], False

            rows = conn.execute(
                FREE_SQL.format(where=""), {"start": start, "end": end}
            ).fetchall()
            best = sorted(rows, key=lambda row: (-row["free_spaces"], row["zone"]))
            if not best or best[0]["free_spaces"] <= 0:
                conn.execute("ROLLBACK")
                raise NoSpaceAvailable(f"No space is free from {start} to {end}")

            zone = best[0]["zone"]
            conn.execute(
                "INSERT INTO bookings (request_id, zone, car_number, period_start, period_end) "
                "VALUES (?, ?, ?, ?, ?)",
                (request_id, zone, car_number, start, end),
            )
            conn.execute("COMMIT")
            return zone, True
        except BaseException:
            if conn.in_transaction:
                conn.execute("ROLLBACK")
            raise
    finally:
        conn.close()


def allocate_for(record: dict, db_path=DB_PATH):
    """Reserve a space for an approved reservation record from the admin service."""
    return allocate(record["id"], record["car_number"], record["start"], record["end"], db_path)