import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).resolve().parent.parent / "data" / "parking.db"


def seed() -> None:
    DB_PATH.parent.mkdir(exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    cur.executescript(
        """
        DROP TABLE IF EXISTS working_hours;
        DROP TABLE IF EXISTS prices;
        DROP TABLE IF EXISTS availability;

        CREATE TABLE working_hours (
            day TEXT PRIMARY KEY,
            open_time TEXT NOT NULL,
            close_time TEXT NOT NULL
        );

        CREATE TABLE prices (
            vehicle_type TEXT PRIMARY KEY,
            hourly_rate INTEGER NOT NULL,
            daily_rate INTEGER NOT NULL
        );

        CREATE TABLE availability (
            zone TEXT PRIMARY KEY,
            total_spaces INTEGER NOT NULL,
            available_spaces INTEGER NOT NULL
        );
        """
    )

    days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
    cur.executemany(
        "INSERT INTO working_hours VALUES (?, ?, ?)",
        [(d, "06:00", "23:00") for d in days],
    )

    cur.executemany(
        "INSERT INTO prices VALUES (?, ?, ?)",
        [("car", 40, 300), ("two_wheeler", 15, 100), ("ev_car", 60, 450)],
    )

    cur.executemany(
        "INSERT INTO availability VALUES (?, ?, ?)",
        [("Zone A", 60, 22), ("Zone B", 80, 35), ("Zone C", 40, 9)],
    )

    conn.commit()
    conn.close()
    print(f"Database created at {DB_PATH}")


if __name__ == "__main__":
    seed()