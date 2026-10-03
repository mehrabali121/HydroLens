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
    """Calculate valid consecutive-day positive rises."""
    result = dataframe.copy()

    result["elapsed_days"] = (
        result.groupby("station_id")["observation_date"]
        .diff()
        .dt.total_seconds()
        .div(86400)
    )

    result["level_change_m"] = (
        result.groupby("station_id")["water_level_m"]
        .diff()
    )

    result = result[
        result["elapsed_days"] == 1
    ].copy()

    result["rate_m_per_day"] = (
        result["level_change_m"]
        / result["elapsed_days"]
    )

    result = result[
        result["level_change_m"] > 0
    ].copy()

    return result


def calculate_thresholds(
    rises: pd.DataFrame,
) -> dict[str, float]:
    """Calculate station-specific 95th-percentile thresholds."""
    thresholds = {}

    for station_id in STATIONS:
        station_rises = rises[
            rises["station_id"] == station_id
        ]

        thresholds[station_id] = (
            station_rises["level_change_m"]
            .quantile(PERCENTILE)
        )

    return thresholds


def identify_candidate_events(
    station_data: pd.DataFrame,
    threshold: float,
    allowed_gap_days: int,
) -> pd.DataFrame:
    """
    Group qualifying rise days into candidate events.

    A qualifying day can be separated from the next qualifying
    day by at most allowed_gap_days non-qualifying calendar days.
    """
    qualifying = station_data[
        station_data["level_change_m"] >= threshold
    ].copy()

    if qualifying.empty:
        return pd.DataFrame()

    qualifying = qualifying.sort_values(
        "observation_date"
    ).reset_index(drop=True)

    qualifying["date_difference"] = (
        qualifying["observation_date"]
        .diff()
        .dt.days
    )

    qualifying["event_group"] = (
        qualifying["date_difference"]
        .gt(allowed_gap_days + 1)
        .cumsum()
    )

    events = []

    for _, group in qualifying.groupby("event_group"):
        event_start = group["observation_date"].min()
        event_end = group["observation_date"].max()

        event_window = station_data[
            (
                station_data["observation_date"]
                >= event_start
            )
            & (
                station_data["observation_date"]
                <= event_end
            )
        ].copy()

        peak_row = event_window.loc[
            event_window["water_level_m"].idxmax()
        ]

        start_level = event_window.iloc[0]["water_level_m"]

        peak_level = peak_row["water_level_m"]

        actual_rise_to_peak = (
            peak_level - start_level
        )

        events.append(
            {
                "event_start": event_start,
                "event_end": event_end,
                "qualifying_rise_days": len(group),
                "peak_date": peak_row[
                    "observation_date"
                ],
                "actual_rise_to_peak_m": (
                    actual_rise_to_peak
                ),
                "largest_daily_rise_m": (
                    group["level_change_m"].max()
                ),
                "total_qualifying_rise_m": (
                    group["level_change_m"].sum()
                ),
            }
        )

    return pd.DataFrame(events)


def show_clustering_comparison(
    rises: pd.DataFrame,
    thresholds: dict[str, float],
) -> None:
    """Compare zero-gap and one-gap event clustering."""
    print(
        "1. 95th-percentile clustering comparison"
    )

    for station_id in STATIONS:
        station_rises = rises[
            rises["station_id"] == station_id
        ]

        threshold = thresholds[station_id]

        print(f"\n   {station_id}")
        print(
            f"      Threshold: {threshold:.3f} m"
        )

        for allowed_gap_days in [0, 1]:
            events = identify_candidate_events(
                station_rises,
                threshold,
                allowed_gap_days,
            )

            multi_day_events = (
                events["qualifying_rise_days"] > 1
            ).sum()

            print(
                f"      "
                f"{allowed_gap_days}-day gap tolerance: "
                f"{len(events)} events, "
                f"{multi_day_events} multi-qualifying-day events"
            )


def show_event_examples(
    rises: pd.DataFrame,
    thresholds: dict[str, float],
) -> None:
    """Show the largest candidate events using one-day tolerance."""
    print(
        "\n2. Largest candidate events "
        "with one-day tolerance"
    )

    for station_id in STATIONS:
        station_rises = rises[
            rises["station_id"] == station_id
        ]

        threshold = thresholds[station_id]

        events = identify_candidate_events(
            station_rises,
            threshold,
            allowed_gap_days=1,
        )

        events = events.sort_values(
            "actual_rise_to_peak_m",
            ascending=False,
        )

        print(f"\n   {station_id}")

        for _, event in events.head(10).iterrows():
            print(
                f"      "
                f"{event['event_start'].date()} "
                f"to "
                f"{event['event_end'].date()} | "
                f"peak "
                f"{event['peak_date'].date()} | "
                f"{int(event['qualifying_rise_days'])} "
                f"qualifying day(s) | "
                f"actual rise to peak "
                f"+{event['actual_rise_to_peak_m']:.3f} m | "
                f"largest daily rise "
                f"+{event['largest_daily_rise_m']:.3f} m"
            )


def show_event_lengths(
    rises: pd.DataFrame,
    thresholds: dict[str, float],
) -> None:
    """Show candidate event duration statistics."""
    print(
        "\n3. Candidate event duration "
        "with one-day tolerance"
    )

    for station_id in STATIONS:
        station_rises = rises[
            rises["station_id"] == station_id
        ]

        threshold = thresholds[station_id]

        events = identify_candidate_events(
            station_rises,
            threshold,
            allowed_gap_days=1,
        )

        if events.empty:
            continue

        duration_days = (
            events["event_end"]
            - events["event_start"]
        ).dt.days + 1

        print(f"\n   {station_id}")
        print(
            f"      Events: {len(events)}"
        )
        print(
            f"      Median duration: "
            f"{duration_days.median():.1f} days"
        )
        print(
            f"      Maximum duration: "
            f"{duration_days.max()} days"
        )
        print(
            f"      90th percentile duration: "
            f"{duration_days.quantile(0.90):.1f} days"
        )


def main() -> None:
    """Run candidate event clustering analysis."""
    if not DATABASE_PATH.exists():
        raise FileNotFoundError(
            f"Database does not exist: {DATABASE_PATH}"
        )

    dataframe = load_daily_observations()

    rises = calculate_daily_rises(
        dataframe
    )

    thresholds = calculate_thresholds(
        rises
    )

    show_clustering_comparison(
        rises,
        thresholds,
    )

    show_event_examples(
        rises,
        thresholds,
    )

    show_event_lengths(
        rises,
        thresholds,
    )


if __name__ == "__main__":
    main()