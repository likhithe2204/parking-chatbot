import sqlite3

from app.seed_db import seed


def _count(path, table):
    conn = sqlite3.connect(path)
    try:
        return conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
    finally:
        conn.close()


def test_seed_creates_all_tables_with_rows(tmp_path):
    path = tmp_path / "t.db"
    seed(path)
    assert _count(path, "working_hours") == 7
    assert _count(path, "prices") == 3
    assert _count(path, "availability") == 3


def test_seed_can_run_twice_without_duplicates(tmp_path):
    path = tmp_path / "t.db"
    seed(path)
    seed(path)
    assert _count(path, "availability") == 3


def test_available_spaces_never_exceed_total(tmp_path):
    path = tmp_path / "t.db"
    seed(path)
    conn = sqlite3.connect(path)
    try:
        rows = conn.execute(
            "SELECT total_spaces, available_spaces FROM availability"
        ).fetchall()
    finally:
        conn.close()
    assert all(available <= total for total, available in rows)