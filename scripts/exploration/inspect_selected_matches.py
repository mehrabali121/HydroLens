from pathlib import Path

import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[2]
EPISODE_FILE = PROJECT_ROOT / "data" / "processed" / "events" / "rise_episodes.csv"

UPSTREAM_STATION = "01AF002"
DOWNSTREAM_STATIONS = [
    "01AK003",
    "01AO012",
    "01AP003",
]

MATCH_WINDOW_DAYS = 2


def load_episodes() -> pd.DataFrame:
    """Load and validate the historical rise episodes."""
    if not EPISODE_FILE.exists():
        raise FileNotFoundError(
            f"Episode file not found: {EPISODE_FILE}"
        )

    df = pd.read_csv(EPISODE_FILE)

    required_columns = {
        "episode_id",
        "station_id",
        "episode_start",
        "episode_end",
        "duration_days",
        "trigger_count",
        "first_trigger_date",
        "last_trigger_date",
        "largest_trigger_date",
        "largest_trigger_rise_m",
    }

    missing_columns = required_columns - set(df.columns)

    if missing_columns:
        raise ValueError(
            "Missing required episode columns: "
            + ", ".join(sorted(missing_columns))
        )

    df["episode_start"] = pd.to_datetime(df["episode_start"])
    df["episode_end"] = pd.to_datetime(df["episode_end"])
    df["first_trigger_date"] = pd.to_datetime(df["first_trigger_date"])
    df["last_trigger_date"] = pd.to_datetime(df["last_trigger_date"])
    df["largest_trigger_date"] = pd.to_datetime(df["largest_trigger_date"])

    if not df["episode_id"].is_unique:
        raise ValueError("Episode IDs are not unique.")

    if not (df["episode_start"] == df["first_trigger_date"]).all():
        raise ValueError(
            "Some episode_start values do not match first_trigger_date."
        )

    if not (df["episode_end"] >= df["episode_start"]).all():
        raise ValueError(
            "At least one episode has an end date before its start date."
        )

    return df


def find_candidates(
    upstream: pd.DataFrame,
    downstream: pd.DataFrame,
    window_days: int,
) -> pd.DataFrame:
    """Find downstream episodes beginning within the matching window."""
    upstream = upstream.copy()
    downstream = downstream.copy()

    upstream = upstream.rename(
        columns={
            "episode_id": "upstream_episode_id",
            "station_id": "upstream_station_id",
            "episode_start": "upstream_start_date",
            "episode_end": "upstream_end_date",
            "duration_days": "upstream_duration_days",
            "trigger_count": "upstream_trigger_count",
            "largest_trigger_date": "upstream_largest_rise_date",
            "largest_trigger_rise_m": "upstream_largest_rise_m",
        }
    )

    downstream = downstream.rename(
        columns={
            "episode_id": "downstream_episode_id",
            "station_id": "downstream_station_id",
            "episode_start": "downstream_start_date",
            "episode_end": "downstream_end_date",
            "duration_days": "downstream_duration_days",
            "trigger_count": "downstream_trigger_count",
            "largest_trigger_date": "downstream_largest_rise_date",
            "largest_trigger_rise_m": "downstream_largest_rise_m",
        }
    )

    merged = upstream.merge(
        downstream,
        how="cross",
    )

    merged["start_lag_days"] = (
        merged["downstream_start_date"] - merged["upstream_start_date"]
    ).dt.days

    candidates = merged[
        merged["start_lag_days"].between(0, window_days)
    ].copy()

    candidates["relationship"] = candidates.apply(
        classify_relationship,
        axis=1,
    )

    return candidates


def classify_relationship(row: pd.Series) -> str:
    """Classify whether the downstream episode overlaps the upstream episode."""
    if row["downstream_start_date"] <= row["upstream_end_date"]:
        return "overlap"

    return "follow_up"


def select_nearest_candidates(candidates: pd.DataFrame) -> pd.DataFrame:
    """Select the nearest downstream episode for each upstream episode."""
    if candidates.empty:
        return candidates.copy()

    ordered = candidates.sort_values(
        [
            "upstream_episode_id",
            "start_lag_days",
            "downstream_start_date",
            "downstream_episode_id",
        ]
    )

    selected = (
        ordered
        .groupby("upstream_episode_id", as_index=False)
        .first()
    )

    return selected


def print_pair_summary(
    upstream_station: str,
    downstream_station: str,
    candidates: pd.DataFrame,
    selected: pd.DataFrame,
) -> None:
    """Print detailed inspection information for one station pair."""
    print()
    print("=" * 90)
    print(f"{upstream_station} -> {downstream_station}")
    print("=" * 90)

    print(f"Candidate pairs: {len(candidates)}")
    print(f"Selected matches: {len(selected)}")

    if selected.empty:
        print("No selected matches.")
        return

    duplicate_downstream_count = (
        selected["downstream_episode_id"].duplicated().sum()
    )

    print(
        "Selected downstream episodes reused: "
        f"{duplicate_downstream_count}"
    )

    print()
    print("Selected matches:")
    print("-" * 90)

    display_columns = [
        "upstream_episode_id",
        "upstream_start_date",
        "upstream_end_date",
        "downstream_episode_id",
        "downstream_start_date",
        "downstream_end_date",
        "start_lag_days",
        "relationship",
        "upstream_largest_rise_m",
        "downstream_largest_rise_m",
    ]

    display_df = selected[display_columns].copy()

    display_df["upstream_start_date"] = (
        display_df["upstream_start_date"].dt.strftime("%Y-%m-%d")
    )

    display_df["upstream_end_date"] = (
        display_df["upstream_end_date"].dt.strftime("%Y-%m-%d")
    )

    display_df["downstream_start_date"] = (
        display_df["downstream_start_date"].dt.strftime("%Y-%m-%d")
    )

    display_df["downstream_end_date"] = (
        display_df["downstream_end_date"].dt.strftime("%Y-%m-%d")
    )

    display_df["upstream_largest_rise_m"] = (
        display_df["upstream_largest_rise_m"].round(3)
    )

    display_df["downstream_largest_rise_m"] = (
        display_df["downstream_largest_rise_m"].round(3)
    )

    print(
        display_df.to_string(
            index=False,
            max_colwidth=30,
        )
    )

    print()
    print("Lag distribution:")
    print(
        selected["start_lag_days"]
        .value_counts()
        .sort_index()
        .to_string()
    )

    print()
    print("Relationship distribution:")
    print(
        selected["relationship"]
        .value_counts()
        .sort_index()
        .to_string()
    )

    print()
    print("Largest-rise comparison:")
    print(
        f"  Upstream median: "
        f"{selected['upstream_largest_rise_m'].median():.3f} m"
    )
    print(
        f"  Downstream median: "
        f"{selected['downstream_largest_rise_m'].median():.3f} m"
    )


def inspect_station_pair(
    episodes: pd.DataFrame,
    downstream_station: str,
) -> None:
    """Inspect one upstream/downstream station pair."""
    upstream = episodes[
        episodes["station_id"] == UPSTREAM_STATION
    ].copy()

    downstream = episodes[
        episodes["station_id"] == downstream_station
    ].copy()

    if upstream.empty:
        raise ValueError(
            f"No episodes found for upstream station {UPSTREAM_STATION}."
        )

    if downstream.empty:
        raise ValueError(
            f"No episodes found for downstream station "
            f"{downstream_station}."
        )

    candidates = find_candidates(
        upstream,
        downstream,
        MATCH_WINDOW_DAYS,
    )

    selected = select_nearest_candidates(candidates)

    print_pair_summary(
        UPSTREAM_STATION,
        downstream_station,
        candidates,
        selected,
    )


def main() -> None:
    """Run the 0–2 day historical episode match inspection."""
    print("Loading historical rise episodes...")
    episodes = load_episodes()

    print(f"Episode file: {EPISODE_FILE}")
    print(f"Total episodes: {len(episodes)}")
    print(
        "Matching window: "
        f"0–{MATCH_WINDOW_DAYS} calendar days"
    )

    print()
    print("Episode counts by station:")

    station_counts = (
        episodes["station_id"]
        .value_counts()
        .sort_index()
    )

    print(station_counts.to_string())

    for downstream_station in DOWNSTREAM_STATIONS:
        inspect_station_pair(
            episodes,
            downstream_station,
        )


if __name__ == "__main__":
    main()