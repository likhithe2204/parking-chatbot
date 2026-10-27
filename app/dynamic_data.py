import sqlite3
from pathlib import Path

from app.seed_db import DB_PATH


def _query(sql: str, params: tuple = (), db_path: Path = DB_PATH) -> list[dict]:
    conn = sqlite3.connect(f"{Path(db_path).as_uri()}?mode=ro", uri=True)
    conn.row_factory = sqlite3.Row
    try:
        rows = conn.execute(sql, params).fetchall()
    finally:
        conn.close()
    return [dict(row) for row in rows]


def get_working_hours(day: str | None = None, db_path: Path = DB_PATH) -> list[dict]:
    if day:
        return _query(
            "SELECT * FROM working_hours WHERE day = ?",
            (day.strip().title(),),
            db_path,
        )
    return _query("SELECT * FROM working_hours", db_path=db_path)


def get_prices(vehicle_type: str | None = None, db_path: Path = DB_PATH) -> list[dict]:
    if vehicle_type:
        key = vehicle_type.strip().lower().replace(" ", "_")
        return _query("SELECT * FROM prices WHERE vehicle_type = ?", (key,), db_path)
    return _query("SELECT * FROM prices", db_path=db_path)


def get_availability(zone: str | None = None, db_path: Path = DB_PATH) -> list[dict]:
    if zone:
        return _query(
            "SELECT * FROM availability WHERE zone = ?",
            (zone.strip().title(),),
            db_path,
        )
    return _query("SELECT * FROM availability", db_path=db_path)