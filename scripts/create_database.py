import sqlite3
from pathlib import Path

DATABASE_PATH = Path("data/processed/river_rise.sqlite")

STATIONS = [
    {
        "station_id": "01AF002",
        "station_name": "Saint John River at Grand Falls",
        "river_name": "Saint John River",
        "role": "upstream",
        "latitude": 47.0389,
        "longitude": -67.7397,
    },
    {
        "station_id": "01AK003",
        "station_name": "Saint John River at Fredericton",
        "river_name": "Saint John River",
        "role": "downstream_1",
        "latitude": 45.9661,
        "longitude": -66.6514,
    },
    {
        "station_id": "01AO012",
        "station_name": "Saint John River at Gagetown",
        "river_name": "Saint John River",
        "role": "downstream_2",
        "latitude": 45.7686,
        "longitude": -66.1403,
    },
    {
        "station_id": "01AP003",
        "station_name": "Saint John River at Oak Point",
        "river_name": "Saint John River",
        "role": "downstream_3",
        "latitude": 45.5192,
        "longitude": -66.0764,
    },
]


def create_database() -> None:
    """Create the SQLite database and its initial schema."""
    DATABASE_PATH.parent.mkdir(parents=True, exist_ok=True)

    with sqlite3.connect(DATABASE_PATH) as connection:
        connection.execute("PRAGMA foreign_keys = ON")

        connection.executescript(
            """
            CREATE TABLE IF NOT EXISTS stations (
                station_id TEXT PRIMARY KEY,
                station_name TEXT NOT NULL,
                river_name TEXT NOT NULL,
                role TEXT NOT NULL,
                latitude REAL NOT NULL,
                longitude REAL NOT NULL
            );

            CREATE TABLE IF NOT EXISTS daily_observations (
                station_id TEXT NOT NULL,
                observation_date TEXT NOT NULL,
                water_level_m REAL NOT NULL,
                quality_symbol TEXT NOT NULL DEFAULT '',

                PRIMARY KEY (station_id, observation_date),

                FOREIGN KEY (station_id)
                    REFERENCES stations (station_id)
            );
            """
        )

        for station in STATIONS:
            connection.execute(
                """
                INSERT OR IGNORE INTO stations (
                    station_id,
                    station_name,
                    river_name,
                    role,
                    latitude,
                    longitude
                )
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    station["station_id"],
                    station["station_name"],
                    station["river_name"],
                    station["role"],
                    station["latitude"],
                    station["longitude"],
                ),
            )

        connection.commit()

        table_rows = connection.execute(
            """
            SELECT name
            FROM sqlite_master
            WHERE type = 'table'
            ORDER BY name
            """
        ).fetchall()

        station_count = connection.execute(
            "SELECT COUNT(*) FROM stations"
        ).fetchone()[0]

        observation_count = connection.execute(
            "SELECT COUNT(*) FROM daily_observations"
        ).fetchone()[0]

    print(f"Database created: {DATABASE_PATH}")
    print("\nTables:")
    for (table_name,) in table_rows:
        print(f"  {table_name}")

    print(f"\nStation rows: {station_count}")
    print(f"Daily observation rows: {observation_count}")


if __name__ == "__main__":
    create_database()