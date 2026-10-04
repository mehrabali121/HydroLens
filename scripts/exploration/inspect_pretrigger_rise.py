import sqlite3
from pathlib import Path

import pandas as pd


DATABASE_PATH = Path("data/processed/river_rise.sqlite")

STATIONS = [
    "01AF002",
    "01AK003",
    "01AO012",
    "01AP003",
]

PERCENTILE = 0.95


def load_daily_observations() -> pd.DataFrame:
    """Load daily observations from SQLite."""
    query = """
        SELECT
            station_id,
            observation_date,
            water_level_m
        FROM daily_observations
        ORDER BY
            station_id,
            observation_date
    """

    with sqlite3.connect(DATABASE_PATH) as connection:
        dataframe = pd.read_sql_query(query, connection)

    dataframe["observation_date"] = pd.to_datetime(
        dataframe["observation_date"]
    )

    return dataframe


def calculate_daily_rises(
    dataframe: pd.DataFrame,
) -> pd.DataFrame:
    """Calculate rises only across consecutive daily observations."""
    result = dataframe.copy()

    result["elapsed_days"] = (
        result.groupby("station_id")["observation_date"]
        .diff()
        .dt.total_seconds()
        .div(86400)
    )

    result["daily_change_m"] = (
        result.groupby("station_id")["water_level_m"]
        .diff()
    )

    result = result[
        result["elapsed_days"] == 1
    ].copy()

    return result


def calculate_thresholds(
    rises: pd.DataFrame,
) -> dict[str, float]:
    """Calculate station-specific 95th-percentile positive-rise thresholds."""
    thresholds = {}

    for station_id in STATIONS:
        station_rises = rises[
            (rises["station_id"] == station_id)
            & (rises["daily_change_m"] > 0)
        ]

        thresholds[station_id] = (
            station_rises["daily_change_m"]
            .quantile(PERCENTILE)
        )

    return thresholds


def find_trigger_dates(
    rises: pd.DataFrame,
    thresholds: dict[str, float],
) -> pd.DataFrame:
    """Find the first qualifying rise in each candidate event."""
    triggers = []

    for station_id in STATIONS:
        station = rises[
            rises["station_id"] == station_id
        ].copy()

        station["qualifies"] = (
            station["daily_change_m"]
            >= thresholds[station_id]
        )

        qualifying = station[
            station["qualifies"]
        ].copy()

        if qualifying.empty:
            continue

        previous_qualifying_date = None

        for _, row in qualifying.iterrows():
            current_date = row["observation_date"]

            if (
                previous_qualifying_date is None
                or (current_date - previous_qualifying_date).days > 2
            ):
                triggers.append(
                    {
                        "station_id": station_id,
                        "trigger_date": current_date,
                        "trigger_rise_m": row["daily_change_m"],
                    }
                )

            previous_qualifying_date = current_date

    return pd.DataFrame(triggers)


def show_pretrigger_rise(
    rises: pd.DataFrame,
    triggers: pd.DataFrame,
) -> None:
    """Show how much rise occurred before each trigger."""
    print("Pre-trigger rise inspection")
    print(
        "For each candidate event, inspect the 3 days before "
        "the first qualifying rise."
    )

    print("=" * 72)

    for station_id in STATIONS:
        station_rises = rises[
            rises["station_id"] == station_id
        ].copy()

        station_triggers = triggers[
            triggers["station_id"] == station_id
        ]

        print(f"\n{station_id}")

        for _, trigger in station_triggers.iterrows():
            trigger_date = trigger["trigger_date"]

            window = station_rises[
                (
                    station_rises["observation_date"]
                    >= trigger_date - pd.Timedelta(days=3)
                )
                & (
                    station_rises["observation_date"]
                    <= trigger_date
                )
            ].copy()

            if window.empty:
                continue

            print(
                f"\n   Trigger: {trigger_date.date()} "
                f"(+{trigger['trigger_rise_m']:.3f} m)"
            )

            for _, row in window.iterrows():
                marker = (
                    "TRIGGER"
                    if row["observation_date"] == trigger_date
                    else ""
                )

                print(
                    f"      "
                    f"{row['observation_date'].date()} | "
                    f"{row['daily_change_m']:+.3f} m | "
                    f"{marker}"
                )


def main() -> None:
    """Run pre-trigger rise inspection."""
    if not DATABASE_PATH.exists():
        raise FileNotFoundError(
            f"Database does not exist: {DATABASE_PATH}"
        )

    dataframe = load_daily_observations()

    rises = calculate_daily_rises(dataframe)

    thresholds = calculate_thresholds(rises)

    triggers = find_trigger_dates(
        rises,
        thresholds,
    )

    show_pretrigger_rise(
        rises,
        triggers,
    )


if __name__ == "__main__":
    main()