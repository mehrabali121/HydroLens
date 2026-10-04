import sqlite3
from pathlib import Path

import pandas as pd


DATABASE_PATH = Path("data/processed/river_rise.sqlite")


def load_daily_observations() -> pd.DataFrame:
    """Load daily observations and station metadata from SQLite."""
    query = """
        SELECT
            d.station_id,
            s.station_name,
            s.role,
            d.observation_date,
            d.water_level_m,
            d.quality_symbol
        FROM daily_observations AS d
        INNER JOIN stations AS s
            ON d.station_id = s.station_id
        ORDER BY
            d.station_id,
            d.observation_date
    """

    with sqlite3.connect(DATABASE_PATH) as connection:
        dataframe = pd.read_sql_query(query, connection)

    dataframe["observation_date"] = pd.to_datetime(
        dataframe["observation_date"]
    )

    return dataframe


def show_dataset_overview(dataframe: pd.DataFrame) -> None:
    """Display the basic structure of the analysis dataset."""
    print("1. Dataset overview")
    print(f"   Rows: {len(dataframe)}")
    print(f"   Columns: {len(dataframe.columns)}")
    print(
        f"   Date range: "
        f"{dataframe['observation_date'].min().date()}"
    )
    print(
        f"              to "
        f"{dataframe['observation_date'].max().date()}"
    )

    print("\n   Columns and data types:")
    for column_name, data_type in dataframe.dtypes.items():
        print(f"      {column_name}: {data_type}")


def show_missing_values(dataframe: pd.DataFrame) -> None:
    """Display missing values in each analysis column."""
    missing_counts = dataframe.isna().sum()

    print("\n2. Missing values")

    for column_name, missing_count in missing_counts.items():
        print(f"   {column_name}: {missing_count}")


def show_station_summary(dataframe: pd.DataFrame) -> None:
    """Display observation and water-level summaries by station."""
    summary = (
        dataframe.groupby(
            ["station_id", "station_name", "role"],
            sort=True,
        )
        .agg(
            observations=("water_level_m", "count"),
            first_date=("observation_date", "min"),
            last_date=("observation_date", "max"),
            minimum_level_m=("water_level_m", "min"),
            maximum_level_m=("water_level_m", "max"),
            mean_level_m=("water_level_m", "mean"),
            median_level_m=("water_level_m", "median"),
        )
        .reset_index()
    )

    print("\n3. Station summary")

    for _, row in summary.iterrows():
        print(f"\n   {row['station_id']} — {row['station_name']}")
        print(f"      Role: {row['role']}")
        print(f"      Observations: {row['observations']}")
        print(
            f"      Date range: "
            f"{row['first_date'].date()} "
            f"to {row['last_date'].date()}"
        )
        print(
            f"      Minimum: {row['minimum_level_m']:.3f} m"
        )
        print(
            f"      Maximum: {row['maximum_level_m']:.3f} m"
        )
        print(
            f"      Mean: {row['mean_level_m']:.3f} m"
        )
        print(
            f"      Median: {row['median_level_m']:.3f} m"
        )


def show_quality_summary(dataframe: pd.DataFrame) -> None:
    """Display quality-symbol counts by station."""
    summary = (
        dataframe.groupby(
            ["station_id", "quality_symbol"],
            dropna=False,
        )
        .size()
        .reset_index(name="observations")
        .sort_values(
            ["station_id", "quality_symbol"]
        )
    )

    print("\n4. Quality-symbol summary")

    for station_id in dataframe["station_id"].unique():
        station_rows = summary[
            summary["station_id"] == station_id
        ]

        print(f"   {station_id}:")

        for _, row in station_rows.iterrows():
            symbol = row["quality_symbol"]

            if symbol == "":
                symbol = "(blank)"

            print(
                f"      {symbol}: "
                f"{row['observations']}"
            )


def calculate_observation_changes(
    dataframe: pd.DataFrame,
) -> pd.DataFrame:
    """Calculate changes and elapsed time between observations."""
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
        result["level_change_m"] / result["elapsed_days"]
    )

    return result


def show_coverage_summary(dataframe: pd.DataFrame) -> None:
    """Show calendar-day coverage and missing periods by station."""
    print("\n5. Calendar-day coverage")

    expected_dates = pd.date_range(
        dataframe["observation_date"].min(),
        dataframe["observation_date"].max(),
        freq="D",
    )

    expected_days = len(expected_dates)

    for station_id, station_data in dataframe.groupby(
        "station_id",
        sort=True,
    ):
        actual_dates = pd.DatetimeIndex(
            station_data["observation_date"]
        )

        missing_dates = expected_dates.difference(actual_dates)

        coverage_percent = (
            len(actual_dates) / expected_days * 100
        )

        print(
            f"   {station_id}: "
            f"{len(actual_dates)}/{expected_days} days "
            f"({coverage_percent:.2f}%)"
        )

        print(
            f"      Missing days: {len(missing_dates)}"
        )

        if len(missing_dates) > 0:
            print(
                f"      First missing date: "
                f"{missing_dates[0].date()}"
            )
            print(
                f"      Last missing date: "
                f"{missing_dates[-1].date()}"
            )


def show_distribution_summary(dataframe: pd.DataFrame) -> None:
    """Show distribution statistics for each station."""
    summary = (
        dataframe.groupby("station_id")["water_level_m"]
        .quantile(
            [
                0.01,
                0.05,
                0.25,
                0.50,
                0.75,
                0.95,
                0.99,
            ]
        )
        .unstack()
    )

    print("\n6. Water-level distribution")

    for station_id, row in summary.iterrows():
        print(f"   {station_id}:")
        print(f"      1st percentile:  {row[0.01]:.3f} m")
        print(f"      5th percentile:  {row[0.05]:.3f} m")
        print(f"      25th percentile: {row[0.25]:.3f} m")
        print(f"      50th percentile: {row[0.50]:.3f} m")
        print(f"      75th percentile: {row[0.75]:.3f} m")
        print(f"      95th percentile: {row[0.95]:.3f} m")
        print(f"      99th percentile: {row[0.99]:.3f} m")


def show_observation_spacing(
    dataframe: pd.DataFrame,
) -> None:
    """Show spacing between consecutive observations."""
    result = calculate_observation_changes(dataframe)

    print("\n7. Observation spacing")

    for station_id, station_data in result.groupby(
        "station_id",
        sort=True,
    ):
        spacing = station_data["elapsed_days"].dropna()

        print(f"   {station_id}:")
        print(f"      Observation intervals: {len(spacing)}")
        print(
            f"      Minimum interval: "
            f"{spacing.min():.0f} day(s)"
        )
        print(
            f"      Median interval: "
            f"{spacing.median():.0f} day(s)"
        )
        print(
            f"      Maximum interval: "
            f"{spacing.max():.0f} day(s)"
        )

        longer_than_one_day = station_data[
            station_data["elapsed_days"] > 1
        ].copy()

        print(
            f"      Intervals longer than 1 day: "
            f"{len(longer_than_one_day)}"
        )

        for _, row in longer_than_one_day.iterrows():
            previous_date = (
                row["observation_date"]
                - pd.to_timedelta(
                    row["elapsed_days"],
                    unit="D",
                )
            )

            print(
                f"         "
                f"{previous_date.date()} "
                f"to "
                f"{row['observation_date'].date()}: "
                f"{row['elapsed_days']:.0f} day(s)"
            )


def show_change_summary(
    dataframe: pd.DataFrame,
) -> None:
    """Show level-change and rate-of-change distributions."""
    result = calculate_observation_changes(dataframe)

    print("\n8. Change and rate summary")

    for station_id, station_data in result.groupby(
        "station_id",
        sort=True,
    ):
        valid_changes = station_data.dropna(
            subset=[
                "level_change_m",
                "rate_m_per_day",
            ]
        )

        change_quantiles = valid_changes[
            "level_change_m"
        ].quantile(
            [
                0.01,
                0.05,
                0.50,
                0.95,
                0.99,
            ]
        )

        rate_quantiles = valid_changes[
            "rate_m_per_day"
        ].quantile(
            [
                0.01,
                0.05,
                0.50,
                0.95,
                0.99,
            ]
        )

        print(f"   {station_id}:")

        print(
            "      Level change "
            "(m between observations):"
        )
        print(
            f"         1st percentile:  "
            f"{change_quantiles[0.01]:.3f}"
        )
        print(
            f"         5th percentile:  "
            f"{change_quantiles[0.05]:.3f}"
        )
        print(
            f"         Median:           "
            f"{change_quantiles[0.50]:.3f}"
        )
        print(
            f"         95th percentile: "
            f"{change_quantiles[0.95]:.3f}"
        )
        print(
            f"         99th percentile: "
            f"{change_quantiles[0.99]:.3f}"
        )

        print(
            "      Rate of change "
            "(m/day):"
        )
        print(
            f"         1st percentile:  "
            f"{rate_quantiles[0.01]:.3f}"
        )
        print(
            f"         5th percentile:  "
            f"{rate_quantiles[0.05]:.3f}"
        )
        print(
            f"         Median:           "
            f"{rate_quantiles[0.50]:.3f}"
        )
        print(
            f"         95th percentile: "
            f"{rate_quantiles[0.95]:.3f}"
        )
        print(
            f"         99th percentile: "
            f"{rate_quantiles[0.99]:.3f}"
        )


def show_largest_rises(
    dataframe: pd.DataFrame,
) -> None:
    """Show the largest rises while displaying elapsed time."""
    result = calculate_observation_changes(dataframe)

    rises = result[
        result["level_change_m"] > 0
    ].copy()

    print("\n9. Largest observed rises")

    for station_id, station_data in rises.groupby(
        "station_id",
        sort=True,
    ):
        largest = station_data.nlargest(
            5,
            "level_change_m",
        )

        print(f"   {station_id}:")

        for _, row in largest.iterrows():
            print(
                f"      "
                f"{row['observation_date'].date()}: "
                f"+{row['level_change_m']:.3f} m "
                f"over {row['elapsed_days']:.0f} day(s) "
                f"({row['rate_m_per_day']:.3f} m/day)"
            )


def show_largest_rates(
    dataframe: pd.DataFrame,
) -> None:
    """Show the largest positive rates of water-level rise."""
    result = calculate_observation_changes(dataframe)

    rises = result[
        result["rate_m_per_day"] > 0
    ].copy()

    print("\n10. Largest positive rates of rise")

    for station_id, station_data in rises.groupby(
        "station_id",
        sort=True,
    ):
        largest = station_data.nlargest(
            5,
            "rate_m_per_day",
        )

        print(f"   {station_id}:")

        for _, row in largest.iterrows():
            print(
                f"      "
                f"{row['observation_date'].date()}: "
                f"+{row['rate_m_per_day']:.3f} m/day "
                f"({row['level_change_m']:.3f} m "
                f"over {row['elapsed_days']:.0f} day(s))"
            )


def main() -> None:
    """Run the daily exploratory analysis."""
    if not DATABASE_PATH.exists():
        raise FileNotFoundError(
            f"Database does not exist: {DATABASE_PATH}"
        )

    dataframe = load_daily_observations()

    show_dataset_overview(dataframe)
    show_missing_values(dataframe)
    show_station_summary(dataframe)
    show_quality_summary(dataframe)
    show_coverage_summary(dataframe)
    show_distribution_summary(dataframe)
    show_observation_spacing(dataframe)
    show_change_summary(dataframe)
    show_largest_rises(dataframe)
    show_largest_rates(dataframe)


if __name__ == "__main__":
    main()