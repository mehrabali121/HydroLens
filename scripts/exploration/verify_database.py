import sqlite3
from pathlib import Path

DATABASE_PATH = Path("data/processed/river_rise.sqlite")


def verify_total_rows(connection: sqlite3.Connection) -> None:
    """Verify the total number of daily observations."""
    total_rows = connection.execute(
        "SELECT COUNT(*) FROM daily_observations"
    ).fetchone()[0]

    print("1. Total observations")
    print(f"   {total_rows}")


def verify_station_counts(connection: sqlite3.Connection) -> None:
    """Show the number of observations stored for each station."""
    rows = connection.execute(
        """
        SELECT station_id, COUNT(*) AS observation_count
        FROM daily_observations
        GROUP BY station_id
        ORDER BY station_id
        """
    ).fetchall()

    print("\n2. Observations by station")
    for station_id, observation_count in rows:
        print(f"   {station_id}: {observation_count}")


def verify_date_ranges(connection: sqlite3.Connection) -> None:
    """Show the first and last observation date for each station."""
    rows = connection.execute(
        """
        SELECT
            station_id,
            MIN(observation_date) AS first_date,
            MAX(observation_date) AS last_date
        FROM daily_observations
        GROUP BY station_id
        ORDER BY station_id
        """
    ).fetchall()

    print("\n3. Date ranges")
    for station_id, first_date, last_date in rows:
        print(
            f"   {station_id}: "
            f"{first_date} to {last_date}"
        )


def verify_water_level_ranges(connection: sqlite3.Connection) -> None:
    """Show the minimum and maximum water level for each station."""
    rows = connection.execute(
        """
        SELECT
            station_id,
            MIN(water_level_m) AS minimum_level,
            MAX(water_level_m) AS maximum_level
        FROM daily_observations
        GROUP BY station_id
        ORDER BY station_id
        """
    ).fetchall()

    print("\n4. Water-level ranges")
    for station_id, minimum_level, maximum_level in rows:
        print(
            f"   {station_id}: "
            f"{minimum_level:.3f} m to {maximum_level:.3f} m"
        )


def verify_quality_symbols(connection: sqlite3.Connection) -> None:
    """Show the stored quality-symbol counts for each station."""
    rows = connection.execute(
        """
        SELECT
            station_id,
            quality_symbol,
            COUNT(*) AS observation_count
        FROM daily_observations
        GROUP BY station_id, quality_symbol
        ORDER BY station_id, quality_symbol
        """
    ).fetchall()

    print("\n5. Quality symbols")

    current_station = None

    for station_id, quality_symbol, observation_count in rows:
        if station_id != current_station:
            print(f"   {station_id}:")
            current_station = station_id

        displayed_symbol = (
            "(blank)"
            if quality_symbol == ""
            else quality_symbol
        )

        print(
            f"      {displayed_symbol}: "
            f"{observation_count}"
        )


def verify_duplicates(connection: sqlite3.Connection) -> None:
    """Check for duplicate station/date combinations."""
    duplicate_rows = connection.execute(
        """
        SELECT
            station_id,
            observation_date,
            COUNT(*) AS duplicate_count
        FROM daily_observations
        GROUP BY station_id, observation_date
        HAVING COUNT(*) > 1
        ORDER BY station_id, observation_date
        """
    ).fetchall()

    print("\n6. Duplicate station/date records")

    if duplicate_rows:
        print(
            f"   FAIL: {len(duplicate_rows)} "
            "duplicate combinations found."
        )

        for row in duplicate_rows[:10]:
            print(f"   {row}")
    else:
        print("   PASS: no duplicate station/date combinations.")


def verify_foreign_keys(connection: sqlite3.Connection) -> None:
    """Check SQLite foreign-key integrity."""
    violations = connection.execute(
        "PRAGMA foreign_key_check"
    ).fetchall()

    print("\n7. Foreign-key integrity")

    if violations:
        print(
            f"   FAIL: {len(violations)} "
            "foreign-key violations found."
        )

        for violation in violations[:10]:
            print(f"   {violation}")
    else:
        print("   PASS: no foreign-key violations.")


def verify_station_join(connection: sqlite3.Connection) -> None:
    """Verify that observations join correctly to station metadata."""
    rows = connection.execute(
        """
        SELECT
            s.station_id,
            s.station_name,
            s.role,
            COUNT(d.observation_date) AS observation_count
        FROM stations AS s
        LEFT JOIN daily_observations AS d
            ON d.station_id = s.station_id
        GROUP BY
            s.station_id,
            s.station_name,
            s.role
        ORDER BY s.station_id
        """
    ).fetchall()

    print("\n8. Station metadata JOIN")

    for station_id, station_name, role, observation_count in rows:
        print(
            f"   {station_id} | "
            f"{role} | "
            f"{observation_count} observations | "
            f"{station_name}"
        )


def main() -> None:
    """Run database verification checks."""
    if not DATABASE_PATH.exists():
        raise FileNotFoundError(
            f"Database does not exist: {DATABASE_PATH}"
        )

    with sqlite3.connect(DATABASE_PATH) as connection:
        connection.execute("PRAGMA foreign_keys = ON")

        print(f"Database: {DATABASE_PATH}")

        verify_total_rows(connection)
        verify_station_counts(connection)
        verify_date_ranges(connection)
        verify_water_level_ranges(connection)
        verify_quality_symbols(connection)
        verify_duplicates(connection)
        verify_foreign_keys(connection)
        verify_station_join(connection)


if __name__ == "__main__":
    main()