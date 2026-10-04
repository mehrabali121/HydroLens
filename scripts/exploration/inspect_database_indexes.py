import sqlite3
from pathlib import Path

DATABASE_PATH = Path("data/processed/river_rise.sqlite")


def show_indexes(connection: sqlite3.Connection) -> None:
    """Show indexes defined for the database tables."""
    rows = connection.execute(
        """
        SELECT
            name,
            tbl_name,
            sql
        FROM sqlite_master
        WHERE type = 'index'
        ORDER BY tbl_name, name
        """
    ).fetchall()

    print("1. Database indexes")

    if not rows:
        print("   No explicit indexes found.")
        return

    for name, table_name, sql in rows:
        print(f"   {name}")
        print(f"      table: {table_name}")
        print(f"      definition: {sql}")


def show_primary_key_columns(connection: sqlite3.Connection) -> None:
    """Show the daily-observations primary-key columns."""
    rows = connection.execute(
        "PRAGMA table_info(daily_observations)"
    ).fetchall()

    print("\n2. daily_observations schema")

    for row in rows:
        column_id, name, data_type, not_null, default_value, primary_key = row

        if primary_key:
            print(
                f"   Primary-key column {primary_key}: "
                f"{name} ({data_type})"
            )


def show_station_date_query_plan(
    connection: sqlite3.Connection,
) -> None:
    """Inspect the query plan for a station/date time-series query."""
    rows = connection.execute(
        """
        EXPLAIN QUERY PLAN
        SELECT observation_date, water_level_m
        FROM daily_observations
        WHERE station_id = ?
        ORDER BY observation_date
        """,
        ("01AF002",),
    ).fetchall()

    print("\n3. Station/date query plan")

    for row in rows:
        print(f"   {row}")


def show_date_query_plan(
    connection: sqlite3.Connection,
) -> None:
    """Inspect the query plan for a date-only query."""
    rows = connection.execute(
        """
        EXPLAIN QUERY PLAN
        SELECT station_id, observation_date, water_level_m
        FROM daily_observations
        WHERE observation_date BETWEEN ? AND ?
        ORDER BY observation_date
        """,
        ("2020-01-01", "2020-12-31"),
    ).fetchall()

    print("\n4. Date-range query plan")

    for row in rows:
        print(f"   {row}")


def verify_database_integrity(
    connection: sqlite3.Connection,
) -> None:
    """Run SQLite's built-in integrity check."""
    result = connection.execute(
        "PRAGMA integrity_check"
    ).fetchone()[0]

    print("\n5. SQLite integrity check")
    print(f"   {result}")


def main() -> None:
    """Inspect database indexes and query plans."""
    if not DATABASE_PATH.exists():
        raise FileNotFoundError(
            f"Database does not exist: {DATABASE_PATH}"
        )

    with sqlite3.connect(DATABASE_PATH) as connection:
        show_indexes(connection)
        show_primary_key_columns(connection)
        show_station_date_query_plan(connection)
        show_date_query_plan(connection)
        verify_database_integrity(connection)


if __name__ == "__main__":
    main()