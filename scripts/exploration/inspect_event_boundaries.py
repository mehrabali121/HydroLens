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

# Historical events that appear across multiple stations.
EVENT_WINDOWS = [
    ("2012-03-21", "2012-03-27"),
    ("2014-04-12", "2014-04-21"),
    ("2018-04-23", "2018-05-04"),
    ("2019-04-18", "2019-04-26"),
    ("2020-11-29", "2020-12-06"),
    ("2023-04-12", "2023-04-22"),
    ("2023-12-08", "2023-12-16"),
    ("2024-03-26", "2024-04-03"),
]


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
    """Calculate valid consecutive-day water-level changes."""
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

    return result


def calculate_thresholds(
    dataframe: pd.DataFrame,
) -> dict[str, float]:
    """Calculate station-specific 95th-percentile rise thresholds."""
    valid_changes = dataframe[
        dataframe["elapsed_days"] == 1
    ].copy()

    positive_changes = valid_changes[
        valid_changes["daily_change_m"] > 0
    ]

    thresholds = {}

    for station_id in STATIONS:
        station_changes = positive_changes[
            positive_changes["station_id"] == station_id
        ]

        thresholds[station_id] = (
            station_changes["daily_change_m"]
            .quantile(PERCENTILE)
        )

    return thresholds


def show_event_window(
    dataframe: pd.DataFrame,
    thresholds: dict[str, float],
    station_id: str,
    start_date: str,
    end_date: str,
) -> None:
    """Print observations for one station and event window."""
    station_data = dataframe[
        dataframe["station_id"] == station_id
    ].copy()

    start = pd.Timestamp(start_date)
    end = pd.Timestamp(end_date)

    window = station_data[
        (
            station_data["observation_date"]
            >= start
        )
        & (
            station_data["observation_date"]
            <= end
        )
    ].copy()

    if window.empty:
        print(
            f"      No observations for "
            f"{station_id}"
        )
        return

    threshold = thresholds[station_id]

    window["qualifies"] = (
        (
            window["daily_change_m"]
            >= threshold
        )
        & (
            window["elapsed_days"]
            == 1
        )
    )

    print(
        f"\n      {station_id} "
        f"(threshold = {threshold:.3f} m)"
    )

    print(
        "      Date        Level(m)   "
        "Change(m)   Qualifies"
    )

    for _, row in window.iterrows():
        date_text = row[
            "observation_date"
        ].strftime("%Y-%m-%d")

        level_text = (
            f"{row['water_level_m']:.3f}"
        )

        if pd.isna(row["daily_change_m"]):
            change_text = "   N/A"
        else:
            change_text = (
                f"{row['daily_change_m']:+.3f}"
            )

        qualifies_text = (
            "YES"
            if row["qualifies"]
            else ""
        )

        print(
            f"      {date_text}   "
            f"{level_text:>7}   "
            f"{change_text:>8}   "
            f"{qualifies_text}"
        )


def main() -> None:
    """Inspect selected historical event windows."""
    if not DATABASE_PATH.exists():
        raise FileNotFoundError(
            f"Database does not exist: {DATABASE_PATH}"
        )

    dataframe = load_daily_observations()

    dataframe = calculate_daily_rises(
        dataframe
    )

    thresholds = calculate_thresholds(
        dataframe
    )

    print(
        "Candidate event boundary inspection"
    )
    print(
        "Using station-specific 95th-percentile "
        "daily-rise thresholds."
    )

    for start_date, end_date in EVENT_WINDOWS:
        print(
            "\n"
            + "=" * 72
        )
        print(
            f"EVENT WINDOW: "
            f"{start_date} to {end_date}"
        )
        print("=" * 72)

        for station_id in STATIONS:
            show_event_window(
                dataframe,
                thresholds,
                station_id,
                start_date,
                end_date,
            )


if __name__ == "__main__":
    main()