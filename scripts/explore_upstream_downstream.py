import sqlite3
from pathlib import Path

import pandas as pd


DATABASE_PATH = Path("data/processed/river_rise.sqlite")

UPSTREAM_STATION = "01AF002"

DOWNSTREAM_STATIONS = [
    "01AK003",
    "01AO012",
    "01AP003",
]

LAGS_TO_TEST = range(0, 11)


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


def calculate_daily_changes(
    dataframe: pd.DataFrame,
) -> pd.DataFrame:
    """Calculate changes only across consecutive calendar days."""
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

    result.loc[
        result["elapsed_days"] != 1,
        "daily_change_m",
    ] = pd.NA

    return result


def prepare_pair(
    dataframe: pd.DataFrame,
    downstream_station: str,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Create aligned level and valid daily-change data."""
    upstream = dataframe[
        dataframe["station_id"] == UPSTREAM_STATION
    ][
        [
            "observation_date",
            "water_level_m",
            "daily_change_m",
            "elapsed_days",
        ]
    ].copy()

    downstream = dataframe[
        dataframe["station_id"] == downstream_station
    ][
        [
            "observation_date",
            "water_level_m",
            "daily_change_m",
            "elapsed_days",
        ]
    ].copy()

    upstream = upstream.rename(
        columns={
            "water_level_m": "upstream_level_m",
            "daily_change_m": "upstream_change_m",
            "elapsed_days": "upstream_elapsed_days",
        }
    )

    downstream = downstream.rename(
        columns={
            "water_level_m": "downstream_level_m",
            "daily_change_m": "downstream_change_m",
            "elapsed_days": "downstream_elapsed_days",
        }
    )

    levels = upstream.merge(
        downstream,
        on="observation_date",
        how="inner",
    )

    changes = levels.dropna(
        subset=[
            "upstream_change_m",
            "downstream_change_m",
        ]
    ).copy()

    return levels, changes


def correlation_at_lag(
    changes: pd.DataFrame,
    lag_days: int,
) -> tuple[float, int]:
    """
    Calculate the correlation between an upstream daily change
    and a downstream daily change occurring later.
    """
    upstream = changes[
        [
            "observation_date",
            "upstream_change_m",
        ]
    ].copy()

    downstream = changes[
        [
            "observation_date",
            "downstream_change_m",
        ]
    ].copy()

    downstream["upstream_reference_date"] = (
        downstream["observation_date"]
        - pd.to_timedelta(lag_days, unit="D")
    )

    merged = upstream.merge(
        downstream,
        left_on="observation_date",
        right_on="upstream_reference_date",
        how="inner",
    )

    if len(merged) < 2:
        return float("nan"), len(merged)

    correlation = merged[
        "upstream_change_m"
    ].corr(
        merged["downstream_change_m"]
    )

    return correlation, len(merged)


def show_pair_overview(
    dataframe: pd.DataFrame,
) -> None:
    """Show aligned-data coverage for each station pair."""
    print("1. Upstream/downstream pair coverage")

    for downstream_station in DOWNSTREAM_STATIONS:
        levels, changes = prepare_pair(
            dataframe,
            downstream_station,
        )

        print(f"\n   {UPSTREAM_STATION} -> {downstream_station}")
        print(f"      Shared level dates: {len(levels)}")
        print(f"      Shared valid change dates: {len(changes)}")

        if len(levels) > 0:
            print(
                f"      First shared date: "
                f"{levels['observation_date'].min().date()}"
            )
            print(
                f"      Last shared date: "
                f"{levels['observation_date'].max().date()}"
            )


def show_level_correlation(
    dataframe: pd.DataFrame,
) -> None:
    """Calculate same-day correlation of water levels."""
    print("\n2. Same-day water-level correlation")

    for downstream_station in DOWNSTREAM_STATIONS:
        levels, _ = prepare_pair(
            dataframe,
            downstream_station,
        )

        correlation = levels[
            "upstream_level_m"
        ].corr(
            levels["downstream_level_m"]
        )

        print(
            f"   {UPSTREAM_STATION} -> "
            f"{downstream_station}: "
            f"r = {correlation:.3f}"
        )


def show_change_correlation(
    dataframe: pd.DataFrame,
) -> None:
    """Calculate same-day correlation of valid daily changes."""
    print("\n3. Same-day daily-change correlation")

    for downstream_station in DOWNSTREAM_STATIONS:
        _, changes = prepare_pair(
            dataframe,
            downstream_station,
        )

        correlation = changes[
            "upstream_change_m"
        ].corr(
            changes["downstream_change_m"]
        )

        print(
            f"   {UPSTREAM_STATION} -> "
            f"{downstream_station}: "
            f"r = {correlation:.3f}"
        )


def show_lagged_correlations(
    dataframe: pd.DataFrame,
) -> None:
    """Calculate valid daily-change correlations across historical lags."""
    print("\n4. Lagged daily-change correlations")

    for downstream_station in DOWNSTREAM_STATIONS:
        _, changes = prepare_pair(
            dataframe,
            downstream_station,
        )

        print(f"\n   {UPSTREAM_STATION} -> {downstream_station}")

        results = []

        for lag_days in LAGS_TO_TEST:
            correlation, pair_count = correlation_at_lag(
                changes,
                lag_days,
            )

            results.append(
                {
                    "lag_days": lag_days,
                    "correlation": correlation,
                    "pair_count": pair_count,
                }
            )

            print(
                f"      Lag {lag_days:2d} day(s): "
                f"r = {correlation:.3f}, "
                f"paired observations = {pair_count}"
            )

        results_dataframe = pd.DataFrame(results).dropna(
            subset=["correlation"]
        )

        if results_dataframe.empty:
            continue

        strongest = results_dataframe.loc[
            results_dataframe["correlation"].abs().idxmax()
        ]

        print(
            f"      Strongest absolute correlation: "
            f"lag {int(strongest['lag_days'])} day(s), "
            f"r = {strongest['correlation']:.3f}"
        )


def show_strongest_lag_summary(
    dataframe: pd.DataFrame,
) -> None:
    """Summarize the strongest absolute lagged correlations."""
    print("\n5. Strongest lag summary")

    for downstream_station in DOWNSTREAM_STATIONS:
        _, changes = prepare_pair(
            dataframe,
            downstream_station,
        )

        results = []

        for lag_days in LAGS_TO_TEST:
            correlation, pair_count = correlation_at_lag(
                changes,
                lag_days,
            )

            if pd.notna(correlation):
                results.append(
                    {
                        "lag_days": lag_days,
                        "correlation": correlation,
                        "pair_count": pair_count,
                    }
                )

        if not results:
            print(
                f"   {UPSTREAM_STATION} -> "
                f"{downstream_station}: no valid results"
            )
            continue

        results_dataframe = pd.DataFrame(results)

        strongest = results_dataframe.loc[
            results_dataframe["correlation"].abs().idxmax()
        ]

        print(
            f"   {UPSTREAM_STATION} -> "
            f"{downstream_station}: "
            f"lag {int(strongest['lag_days'])} day(s), "
            f"r = {strongest['correlation']:.3f}, "
            f"paired observations = "
            f"{int(strongest['pair_count'])}"
        )


def main() -> None:
    """Run exploratory upstream/downstream analysis."""
    if not DATABASE_PATH.exists():
        raise FileNotFoundError(
            f"Database does not exist: {DATABASE_PATH}"
        )

    dataframe = load_daily_observations()
    dataframe = calculate_daily_changes(dataframe)

    show_pair_overview(dataframe)
    show_level_correlation(dataframe)
    show_change_correlation(dataframe)
    show_lagged_correlations(dataframe)
    show_strongest_lag_summary(dataframe)


if __name__ == "__main__":
    main()