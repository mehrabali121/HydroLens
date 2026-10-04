from pathlib import Path

import pandas as pd


EPISODE_PATH = Path(
    "data/processed/events/rise_episodes.csv"
)

UPSTREAM_STATION = "01AF002"

DOWNSTREAM_STATIONS = [
    "01AK003",
    "01AO012",
    "01AP003",
]

MAX_START_LAG_DAYS = 10


def load_episodes() -> pd.DataFrame:
    """Load rise episodes and normalize date fields."""
    if not EPISODE_PATH.exists():
        raise FileNotFoundError(
            f"Episode file does not exist: {EPISODE_PATH}"
        )

    dataframe = pd.read_csv(
        EPISODE_PATH
    )

    for column in [
        "episode_start",
        "episode_end",
        "first_trigger_date",
        "last_trigger_date",
        "largest_trigger_date",
    ]:
        dataframe[column] = pd.to_datetime(
            dataframe[column]
        )

    return dataframe


def classify_temporal_relationship(
    upstream_start: pd.Timestamp,
    upstream_end: pd.Timestamp,
    downstream_start: pd.Timestamp,
    downstream_end: pd.Timestamp,
) -> str:
    """
    Classify the temporal relationship between two episodes.

    overlap:
        Downstream begins before or on the upstream end.

    follow_up:
        Downstream begins after the upstream episode ends.

    otherwise:
        No relevant relationship.
    """
    if downstream_start <= upstream_end:
        return "overlap"

    if downstream_start > upstream_end:
        return "follow_up"

    return "none"


def analyze_pair(
    episodes: pd.DataFrame,
    downstream_station: str,
) -> pd.DataFrame:
    """Generate candidate upstream/downstream episode pairs."""
    upstream = episodes[
        episodes["station_id"] == UPSTREAM_STATION
    ].copy()

    downstream = episodes[
        episodes["station_id"] == downstream_station
    ].copy()

    rows = []

    for _, upstream_episode in upstream.iterrows():
        for _, downstream_episode in downstream.iterrows():
            start_lag = (
                downstream_episode["episode_start"]
                - upstream_episode["episode_start"]
            ).days

            if not (
                0
                <= start_lag
                <= MAX_START_LAG_DAYS
            ):
                continue

            relationship = classify_temporal_relationship(
                upstream_episode["episode_start"],
                upstream_episode["episode_end"],
                downstream_episode["episode_start"],
                downstream_episode["episode_end"],
            )

            rows.append(
                {
                    "upstream_episode_id": (
                        upstream_episode["episode_id"]
                    ),
                    "downstream_episode_id": (
                        downstream_episode["episode_id"]
                    ),
                    "upstream_start": (
                        upstream_episode["episode_start"]
                    ),
                    "upstream_end": (
                        upstream_episode["episode_end"]
                    ),
                    "downstream_start": (
                        downstream_episode["episode_start"]
                    ),
                    "downstream_end": (
                        downstream_episode["episode_end"]
                    ),
                    "start_lag_days": start_lag,
                    "temporal_relationship": relationship,
                }
            )

    return pd.DataFrame(rows)


def summarize_pair(
    matches: pd.DataFrame,
    downstream_station: str,
) -> None:
    """Print temporal relationship statistics."""
    print(
        f"\n{UPSTREAM_STATION} -> "
        f"{downstream_station}"
    )
    print("=" * 65)

    if matches.empty:
        print("No candidate pairs.")
        return

    relationship_counts = (
        matches["temporal_relationship"]
        .value_counts()
    )

    print(
        f"Candidate pairs: {len(matches)}"
    )

    print(
        f"  Overlap: "
        f"{relationship_counts.get('overlap', 0)}"
    )

    print(
        f"  Follow-up: "
        f"{relationship_counts.get('follow_up', 0)}"
    )

    print(
        f"  None: "
        f"{relationship_counts.get('none', 0)}"
    )

    print("\nStart-lag distribution:")

    lag_counts = (
        matches["start_lag_days"]
        .value_counts()
        .sort_index()
    )

    for lag in range(
        MAX_START_LAG_DAYS + 1
    ):
        print(
            f"  {lag:2d} days: "
            f"{lag_counts.get(lag, 0)}"
        )


def show_follow_up_examples(
    matches: pd.DataFrame,
    downstream_station: str,
) -> None:
    """Show downstream episodes beginning after upstream episodes end."""
    follow_ups = matches[
        matches["temporal_relationship"]
        == "follow_up"
    ].copy()

    print(
        f"\nFollow-up examples: "
        f"{UPSTREAM_STATION} -> "
        f"{downstream_station}"
    )
    print("-" * 65)

    if follow_ups.empty:
        print("No follow-up episodes.")
        return

    follow_ups["end_to_start_days"] = (
        follow_ups["downstream_start"]
        - follow_ups["upstream_end"]
    ).dt.days

    preview = follow_ups.sort_values(
        [
            "upstream_start",
            "end_to_start_days",
        ]
    ).head(15)

    for _, row in preview.iterrows():
        print(
            f"{row['upstream_start'].date()} -> "
            f"{row['upstream_end'].date()} | "
            f"{row['downstream_start'].date()} | "
            f"start lag "
            f"{row['start_lag_days']} d | "
            f"end-to-start "
            f"{row['end_to_start_days']} d"
        )


def show_overlap_examples(
    matches: pd.DataFrame,
    downstream_station: str,
) -> None:
    """Show overlapping candidate episodes."""
    overlaps = matches[
        matches["temporal_relationship"]
        == "overlap"
    ].copy()

    print(
        f"\nOverlap examples: "
        f"{UPSTREAM_STATION} -> "
        f"{downstream_station}"
    )
    print("-" * 65)

    if overlaps.empty:
        print("No overlapping episodes.")
        return

    preview = overlaps.sort_values(
        [
            "upstream_start",
            "start_lag_days",
        ]
    ).head(15)

    for _, row in preview.iterrows():
        print(
            f"{row['upstream_start'].date()} -> "
            f"{row['upstream_end'].date()} | "
            f"{row['downstream_start'].date()} -> "
            f"{row['downstream_end'].date()} | "
            f"start lag "
            f"{row['start_lag_days']} d"
        )


def main() -> None:
    """Analyze temporal relationships between rise episodes."""
    episodes = load_episodes()

    print(
        f"Loaded {len(episodes)} rise episodes."
    )

    print(
        f"Candidate start-date window: "
        f"0-{MAX_START_LAG_DAYS} days"
    )

    for downstream_station in DOWNSTREAM_STATIONS:
        matches = analyze_pair(
            episodes,
            downstream_station,
        )

        summarize_pair(
            matches,
            downstream_station,
        )

        show_follow_up_examples(
            matches,
            downstream_station,
        )

        show_overlap_examples(
            matches,
            downstream_station,
        )


if __name__ == "__main__":
    main()