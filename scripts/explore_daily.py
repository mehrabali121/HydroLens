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
    print(f"   Date range: {dataframe['observation_date'].min().date()}")
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


def main() -> None:
    """Load and inspect the daily analysis dataset."""
    if not DATABASE_PATH.exists():
        raise FileNotFoundError(
            f"Database does not exist: {DATABASE_PATH}"
        )

    dataframe = load_daily_observations()

    show_dataset_overview(dataframe)
    show_missing_values(dataframe)
    show_station_summary(dataframe)
    show_quality_summary(dataframe)


if __name__ == "__main__":
    main()