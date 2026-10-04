from pathlib import Path

import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[1]

EPISODE_PATH = (
    PROJECT_ROOT
    / "data"
    / "processed"
    / "events"
    / "rise_episodes.csv"
)

UPSTREAM_STATION = "01AF002"

DOWNSTREAM_STATIONS = [
    "01AK003",
    "01AO012",
    "01AP003",
]

WINDOWS = [1, 2, 3, 5, 10]


def load_episodes() -> pd.DataFrame:
    """Load and prepare rise episodes for matching analysis."""
    df = pd.read_csv(EPISODE_PATH)

    required_columns = {
        "episode_id",
        "station_id",
        "episode_start",
        "episode_end",
        "duration_days",
        "trigger_count",
        "first_trigger_date",
        "largest_trigger_rise_m",
    }

    missing_columns = required_columns - set(df.columns)

    if missing_columns:
        raise ValueError(
            f"Missing required episode columns: {sorted(missing_columns)}"
        )

    df["episode_start"] = pd.to_datetime(df["episode_start"])
    df["episode_end"] = pd.to_datetime(df["episode_end"])
    df["first_trigger_date"] = pd.to_datetime(df["first_trigger_date"])

    if not (df["episode_start"] == df["first_trigger_date"]).all():
        raise ValueError(
            "Episode start dates do not match first trigger dates."
        )

    return df


def find_candidates(
    upstream: pd.DataFrame,
    downstream: pd.DataFrame,
    window_days: int,
) -> pd.DataFrame:
    """Find downstream episodes whose starts fall within the matching window."""
    rows = []

    for _, upstream_row in upstream.iterrows():
        upstream_start = upstream_row["first_trigger_date"]

        minimum_date = upstream_start
        maximum_date = upstream_start + pd.Timedelta(days=window_days)

        candidates = downstream[
            (downstream["first_trigger_date"] >= minimum_date)
            & (downstream["first_trigger_date"] <= maximum_date)
        ]

        for _, downstream_row in candidates.iterrows():
            downstream_start = downstream_row["first_trigger_date"]

            start_lag_days = (
                downstream_start - upstream_start
            ).days

            rows.append(
                {
                    "upstream_episode_id": upstream_row["episode_id"],
                    "downstream_episode_id": downstream_row["episode_id"],
                    "upstream_start_date": upstream_start,
                    "upstream_end_date": upstream_row["episode_end"],
                    "downstream_start_date": downstream_start,
                    "downstream_end_date": downstream_row["episode_end"],
                    "upstream_duration_days": upstream_row["duration_days"],
                    "downstream_duration_days": downstream_row["duration_days"],
                    "upstream_largest_rise_m": (
                        upstream_row["largest_trigger_rise_m"]
                    ),
                    "downstream_largest_rise_m": (
                        downstream_row["largest_trigger_rise_m"]
                    ),
                    "start_lag_days": start_lag_days,
                }
            )

    return pd.DataFrame(rows)


def select_nearest_candidates(
    candidates: pd.DataFrame,
) -> pd.DataFrame:
    """Select the nearest downstream candidate for each upstream episode."""
    if candidates.empty:
        return candidates.copy()

    selected = (
        candidates.sort_values(
            [
                "upstream_episode_id",
                "start_lag_days",
                "downstream_start_date",
                "downstream_episode_id",
            ]
        )
        .groupby("upstream_episode_id", as_index=False)
        .first()
    )

    return selected


def summarize_window(
    candidates: pd.DataFrame,
    selected: pd.DataFrame,
    window_days: int,
) -> dict:
    """Summarize candidate and nearest-selection results."""
    if candidates.empty:
        return {
            "window_days": window_days,
            "candidate_pairs": 0,
            "upstream_with_candidate": 0,
            "upstream_with_multiple_candidates": 0,
            "nearest_matches": 0,
            "unique_downstream_selected": 0,
            "downstream_selected_multiple_times": 0,
            "median_selected_lag_days": None,
        }

    candidates_per_upstream = candidates.groupby(
        "upstream_episode_id"
    ).size()

    multiple_candidate_count = int(
        (candidates_per_upstream > 1).sum()
    )

    selected_per_downstream = selected.groupby(
        "downstream_episode_id"
    ).size()

    downstream_selected_multiple_times = int(
        (selected_per_downstream > 1).sum()
    )

    return {
        "window_days": window_days,
        "candidate_pairs": len(candidates),
        "upstream_with_candidate": candidates[
            "upstream_episode_id"
        ].nunique(),
        "upstream_with_multiple_candidates": multiple_candidate_count,
        "nearest_matches": len(selected),
        "unique_downstream_selected": selected[
            "downstream_episode_id"
        ].nunique(),
        "downstream_selected_multiple_times": (
            downstream_selected_multiple_times
        ),
        "median_selected_lag_days": selected[
            "start_lag_days"
        ].median(),
    }


def analyze_late_candidates(
    candidates: pd.DataFrame,
    downstream_station: str,
) -> None:
    """Display candidates occurring more than two days after the upstream start."""
    late = candidates[
        candidates["start_lag_days"] > 2
    ].copy()

    print()
    print(
        f"LATE CANDIDATES (>2 DAYS): "
        f"{UPSTREAM_STATION} -> {downstream_station}"
    )

    if late.empty:
        print("None")
        return

    display_columns = [
        "upstream_episode_id",
        "downstream_episode_id",
        "upstream_start_date",
        "upstream_end_date",
        "downstream_start_date",
        "downstream_end_date",
        "start_lag_days",
        "upstream_duration_days",
        "downstream_duration_days",
        "upstream_largest_rise_m",
        "downstream_largest_rise_m",
    ]

    late = late.sort_values(
        [
            "start_lag_days",
            "upstream_start_date",
            "downstream_start_date",
        ]
    )

    print(
        late[display_columns].to_string(index=False)
    )


def analyze_station_pair(
    episodes: pd.DataFrame,
    downstream_station: str,
) -> None:
    """Analyze matching-window sensitivity and nearest selection."""
    upstream = episodes[
        episodes["station_id"] == UPSTREAM_STATION
    ].copy()

    downstream = episodes[
        episodes["station_id"] == downstream_station
    ].copy()

    print()
    print(f"PAIR: {UPSTREAM_STATION} -> {downstream_station}")
    print(f"Upstream episodes: {len(upstream)}")
    print(f"Downstream episodes: {len(downstream)}")

    summaries = []

    for window_days in WINDOWS:
        candidates = find_candidates(
            upstream=upstream,
            downstream=downstream,
            window_days=window_days,
        )

        selected = select_nearest_candidates(candidates)

        summary = summarize_window(
            candidates=candidates,
            selected=selected,
            window_days=window_days,
        )

        summaries.append(summary)

    summary_df = pd.DataFrame(summaries)

    print()
    print(summary_df.to_string(index=False))

    candidates_10_day = find_candidates(
        upstream=upstream,
        downstream=downstream,
        window_days=10,
    )

    analyze_late_candidates(
        candidates=candidates_10_day,
        downstream_station=downstream_station,
    )


def main() -> None:
    episodes = load_episodes()

    print("UPSTREAM/DOWNSTREAM MATCHING WINDOW ANALYSIS")
    print(f"Episode dataset: {EPISODE_PATH}")
    print(f"Upstream station: {UPSTREAM_STATION}")
    print(f"Windows tested: {WINDOWS}")

    for downstream_station in DOWNSTREAM_STATIONS:
        analyze_station_pair(
            episodes=episodes,
            downstream_station=downstream_station,
        )


if __name__ == "__main__":
    main()