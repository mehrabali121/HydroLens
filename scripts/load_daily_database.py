import csv
import sqlite3
from pathlib import Path

DATABASE_PATH = Path("data/processed/river_rise.sqlite")
PROCESSED_DAILY_DIR = Path("data/processed/daily")

STATIONS = [
    "01AF002",
    "01AK003",
    "01AO012",
    "01AP003",
]


def processed_path(station_id: str) -> Path:
    """Return the processed CSV path for one station."""
    return (
        PROCESSED_DAILY_DIR
        / station_id
        / f"{station_id}_daily_20110101_20241231.csv"
    )


def load_station(
    connection: sqlite3.Connection,
    station_id: str,
) -> int:
    """Load one station's processed daily observations."""
    input_path = processed_path(station_id)
    rows_loaded = 0

    with input_path.open(
        "r",
        encoding="utf-8",
        newline="",
    ) as input_file:
        reader = csv.DictReader(input_file)

        for row_number, row in enumerate(reader, start=2):
            if None in row:
                raise ValueError(
                    f"{input_path}: malformed CSV row "
                    f"at line {row_number}."
                )

            if row["station_id"] != station_id:
                raise ValueError(
                    f"{input_path}: unexpected station ID "
                    f"at line {row_number}: "
                    f"{row['station_id']}"
                )

            connection.execute(
                """
                INSERT INTO daily_observations (
                    station_id,
                    observation_date,
                    water_level_m,
                    quality_symbol
                )
                VALUES (?, ?, ?, ?)
                """,
                (
                    row["station_id"],
                    row["date"],
                    float(row["water_level_m"]),
                    row["quality_symbol"],
                ),
            )

            rows_loaded += 1

    return rows_loaded


def main() -> None:
    """Load all processed daily observations into SQLite."""
    if not DATABASE_PATH.exists():
        raise FileNotFoundError(
            f"Database does not exist: {DATABASE_PATH}"
        )

    with sqlite3.connect(DATABASE_PATH) as connection:
        connection.execute("PRAGMA foreign_keys = ON")

        # Remove rows from any earlier run so the pipeline can be
        # run again without hitting the primary key constraint.
        connection.execute("DELETE FROM daily_observations")

        total_rows_loaded = 0

        for station_id in STATIONS:
            rows_loaded = load_station(
                connection=connection,
                station_id=station_id,
            )

            total_rows_loaded += rows_loaded

            print(
                f"Station {station_id}: "
                f"{rows_loaded} rows loaded"
            )

        connection.commit()

    print("\nDatabase loading complete.")
    print(f"Total rows loaded: {total_rows_loaded}")


if __name__ == "__main__":
    main()