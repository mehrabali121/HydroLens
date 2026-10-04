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

PERCENTILES = [0.75, 0.90, 0.95, 0.99]


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


def calculate_valid_daily_rises(
    dataframe: pd.DataFrame,
) -> pd.DataFrame:
    """Calculate rises only across consecutive calendar days."""
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

    result["rate_m_per_day"] = (
        result["level_change_m"]
        / result["elapsed_days"]
    )

    result = result[
        result["elapsed_days"] == 1
    ].copy()

    result["is_rise"] = result["level_change_m"] > 0

    result = result[
        result["is_rise"]
    ].copy()

    return result


def show_rise_distribution(
    dataframe: pd.DataFrame,
) -> None:
    """Show positive daily-rise distribution by station."""
    print("1. Positive daily-rise distribution")

    for station_id in STATIONS:
        station_data = dataframe[
            dataframe["station_id"] == station_id
        ]

        print(f"\n   {station_id}")
        print(
            f"      Positive daily rises: "
            f"{len(station_data)}"
        )

        print(
            f"      Minimum rise: "
            f"{station_data['level_change_m'].min():.3f} m"
        )

        print(
            f"      Maximum rise: "
            f"{station_data['level_change_m'].max():.3f} m"
        )

        print(
            f"      Median rise: "
            f"{station_data['level_change_m'].median():.3f} m"
        )


def show_percentile_thresholds(
    dataframe: pd.DataFrame,
) -> None:
    """Show candidate percentile thresholds."""
    print("\n2. Candidate rise thresholds")

    for station_id in STATIONS:
        station_data = dataframe[
            dataframe["station_id"] == station_id
        ]

        print(f"\n   {station_id}")

        for percentile in PERCENTILES:
            threshold = station_data[
                "level_change_m"
            ].quantile(percentile)

            print(
                f"      {percentile:.0%} percentile: "
                f"{threshold:.3f} m"
            )


def show_event_counts(
    dataframe: pd.DataFrame,
) -> None:
    """Count observations at or above each candidate threshold."""
    print("\n3. Event counts at candidate thresholds")

    for station_id in STATIONS:
        station_data = dataframe[
            dataframe["station_id"] == station_id
        ]

        print(f"\n   {station_id}")

        for percentile in PERCENTILES:
            threshold = station_data[
                "level_change_m"
            ].quantile(percentile)

            event_count = (
                station_data["level_change_m"]
                >= threshold
            ).sum()

            total_rises = len(station_data)

            percentage = (
                event_count / total_rises * 100
            )

            print(
                f"      {percentile:.0%}: "
                f"{event_count} events "
                f"({percentage:.2f}% of positive rises)"
            )


def show_rate_thresholds(
    dataframe: pd.DataFrame,
) -> None:
    """Show candidate rate-of-rise thresholds."""
    print("\n4. Candidate rate-of-rise thresholds")

    for station_id in STATIONS:
        station_data = dataframe[
            dataframe["station_id"] == station_id
        ]

        print(f"\n   {station_id}")

        for percentile in PERCENTILES:
            threshold = station_data[
                "rate_m_per_day"
            ].quantile(percentile)

            print(
                f"      {percentile:.0%} percentile: "
                f"{threshold:.3f} m/day"
            )


def show_rate_event_counts(
    dataframe: pd.DataFrame,
) -> None:
    """Count observations at or above rate thresholds."""
    print("\n5. Event counts at rate-of-rise thresholds")

    for station_id in STATIONS:
        station_data = dataframe[
            dataframe["station_id"] == station_id
        ]

        print(f"\n   {station_id}")

        for percentile in PERCENTILES:
            threshold = station_data[
                "rate_m_per_day"
            ].quantile(percentile)

            event_count = (
                station_data["rate_m_per_day"]
                >= threshold
            ).sum()

            total_rises = len(station_data)

            percentage = (
                event_count / total_rises * 100
            )

            print(
                f"      {percentile:.0%}: "
                f"{event_count} events "
                f"({percentage:.2f}% of positive rises)"
            )


def show_candidate_events(
    dataframe: pd.DataFrame,
) -> None:
    """Show the largest historical rises for context."""
    print("\n6. Largest historical daily rises")

    for station_id in STATIONS:
        station_data = dataframe[
            dataframe["station_id"] == station_id
        ]

        largest = station_data.nlargest(
            10,
            "level_change_m",
        )

        print(f"\n   {station_id}")

        for _, row in largest.iterrows():
            print(
                f"      {row['observation_date'].date()}: "
                f"+{row['level_change_m']:.3f} m "
                f"({row['rate_m_per_day']:.3f} m/day)"
            )


def main() -> None:
    """Run rise-threshold sensitivity analysis."""
    if not DATABASE_PATH.exists():
        raise FileNotFoundError(
            f"Database does not exist: {DATABASE_PATH}"
        )

    dataframe = load_daily_observations()

    rises = calculate_valid_daily_rises(
        dataframe
    )

    show_rise_distribution(rises)
    show_percentile_thresholds(rises)
    show_event_counts(rises)
    show_rate_thresholds(rises)
    show_rate_event_counts(rises)
    show_candidate_events(rises)


if __name__ == "__main__":
    main()