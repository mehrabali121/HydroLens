import sqlite3
from pathlib import Path

import pandas as pd


DATABASE_PATH = Path("data/processed/river_rise.sqlite")
OUTPUT_PATH = Path(
    "data/processed/events/detected_rise_events.csv"
)

STATIONS = [
    "01AF002",
    "01AK003",
    "01AO012",
    "01AP003",
]

RISE_PERCENTILE = 0.95


def load_daily_observations() -> pd.DataFrame:
    """Load daily observations from SQLite."""
    query = """
        SELECT
            station_id,
            observation_date,
            water_level_m,
            quality_symbol
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


def calculate_daily_changes(
    dataframe: pd.DataFrame,
) -> pd.DataFrame:
    """
    Calculate water-level changes only between consecutive
    calendar days within the same station.
    """
    result = dataframe.copy()

    result["elapsed_days"] = (
        result.groupby("station_id")["observation_date"]
        .diff()
        .dt.total_seconds()
        .div(86400)
    )

    result["previous_water_level_m"] = (
        result.groupby("station_id")["water_level_m"]
        .shift(1)
    )

    result["level_change_m"] = (
        result["water_level_m"]
        - result["previous_water_level_m"]
    )

    result = result[
        result["elapsed_days"] == 1
    ].copy()

    return result


def calculate_station_thresholds(
    daily_changes: pd.DataFrame,
    stations: list[str] = STATIONS,
) -> pd.DataFrame:
    """
    Calculate the station-specific threshold from positive
    consecutive-day rises.
    """
    thresholds = []

    for station_id in stations:
        station_data = daily_changes[
            daily_changes["station_id"] == station_id
        ]

        positive_rises = station_data[
            station_data["level_change_m"] > 0
        ]["level_change_m"]

        if positive_rises.empty:
            raise ValueError(
                f"No positive daily rises found for "
                f"station {station_id}."
            )

        threshold = positive_rises.quantile(
            RISE_PERCENTILE
        )

        thresholds.append(
            {
                "station_id": station_id,
                "threshold_m": threshold,
                "positive_rise_count": len(
                    positive_rises
                ),
            }
        )

    return pd.DataFrame(thresholds)


def detect_rise_events(
    daily_changes: pd.DataFrame,
    thresholds: pd.DataFrame,
) -> pd.DataFrame:
    """
    Detect significant daily rise events.

    An event occurs when:
    - the observation is exactly one calendar day after
      the previous observation,
    - the water level increased,
    - and the increase is at or above the station-specific
      95th-percentile positive daily-rise threshold.
    """
    result = daily_changes.merge(
        thresholds[
            ["station_id", "threshold_m"]
        ],
        on="station_id",
        how="left",
        validate="many_to_one",
    )

    result = result[
        result["level_change_m"] > 0
    ].copy()

    result = result[
        result["level_change_m"]
        >= result["threshold_m"]
    ].copy()

    result = result.rename(
        columns={
            "observation_date": "trigger_date",
            "water_level_m": "trigger_level_m",
        }
    )

    result["event_type"] = "significant_daily_rise"

    result = result[
        [
            "station_id",
            "trigger_date",
            "previous_water_level_m",
            "trigger_level_m",
            "level_change_m",
            "threshold_m",
            "quality_symbol",
            "event_type",
        ]
    ].copy()

    result = result.rename(
        columns={
            "level_change_m": "trigger_rise_m",
        }
    )

    result = result.sort_values(
        ["station_id", "trigger_date"]
    ).reset_index(drop=True)

    result["event_id"] = (
        result["station_id"]
        + "_"
        + result["trigger_date"]
        .dt.strftime("%Y%m%d")
    )

    result = result[
        [
            "event_id",
            "station_id",
            "trigger_date",
            "previous_water_level_m",
            "trigger_level_m",
            "trigger_rise_m",
            "threshold_m",
            "quality_symbol",
            "event_type",
        ]
    ]

    return result


def save_events(
    events: pd.DataFrame,
) -> None:
    """Save detected events to a CSV file."""
    OUTPUT_PATH.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    events.to_csv(
        OUTPUT_PATH,
        index=False,
    )


def show_thresholds(
    thresholds: pd.DataFrame,
) -> None:
    """Print the station-specific detection thresholds."""
    print("Station-specific rise thresholds")
    print("=" * 50)

    for _, row in thresholds.iterrows():
        print(
            f"{row['station_id']}: "
            f"{row['threshold_m']:.3f} m "
            f"({RISE_PERCENTILE:.0%} percentile)"
        )


def show_event_summary(
    events: pd.DataFrame,
) -> None:
    """Print the number of detected events by station."""
    print("\nDetected event summary")
    print("=" * 50)

    for station_id in STATIONS:
        station_events = events[
            events["station_id"] == station_id
        ]

        print(
            f"{station_id}: "
            f"{len(station_events)} events"
        )

    print(
        f"\nTotal detected events: {len(events)}"
    )


def show_largest_events(
    events: pd.DataFrame,
) -> None:
    """Print the largest detected daily rises."""
    print("\nLargest detected daily rises")
    print("=" * 50)

    for station_id in STATIONS:
        station_events = events[
            events["station_id"] == station_id
        ]

        largest = station_events.nlargest(
            5,
            "trigger_rise_m",
        )

        print(f"\n{station_id}")

        for _, row in largest.iterrows():
            print(
                f"  {row['trigger_date'].date()}: "
                f"+{row['trigger_rise_m']:.3f} m "
                f"(threshold "
                f"{row['threshold_m']:.3f} m)"
            )


def main() -> None:
    """Run historical significant-rise event detection."""
    if not DATABASE_PATH.exists():
        raise FileNotFoundError(
            f"Database does not exist: "
            f"{DATABASE_PATH}"
        )

    dataframe = load_daily_observations()

    daily_changes = calculate_daily_changes(
        dataframe
    )

    thresholds = calculate_station_thresholds(
        daily_changes
    )

    events = detect_rise_events(
        daily_changes,
        thresholds,
    )

    save_events(events)

    show_thresholds(thresholds)
    show_event_summary(events)
    show_largest_events(events)

    print(
        f"\nSaved detected events to: "
        f"{OUTPUT_PATH}"
    )


if __name__ == "__main__":
    main()