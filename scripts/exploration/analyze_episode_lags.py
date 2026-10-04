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

MAX_LAG_DAYS = 10


def load_episodes() -> pd.DataFrame:
    """Load historical rise episodes."""
    if not EPISODE_PATH.exists():
        raise FileNotFoundError(
            f"Episode file does not exist: {EPISODE_PATH}"
        )

    dataframe = pd.read_csv(
        EPISODE_PATH
    )

    date_columns = [
        "episode_start",
        "episode_end",
        "first_trigger_date",
        "last_trigger_date",
        "largest_trigger_date",
    ]

    for column in date_columns:
        dataframe[column] = pd.to_datetime(
            dataframe[column]
        )

    return dataframe


def analyze_pair(
    episodes: pd.DataFrame,
    downstream_station: str,
) -> pd.DataFrame:
    """
    Compare upstream episode starts with downstream
    episode starts occurring afterward.
    """
    upstream = episodes[
        episodes["station_id"] == UPSTREAM_STATION
    ].copy()

    downstream = episodes[
        episodes["station_id"] == downstream_station
    ].copy()

    rows = []

    for _, upstream_episode in upstream.iterrows():
        for _, downstream_episode in downstream.iterrows():
            lag_days = (
                downstream_episode["episode_start"]
                - upstream_episode["episode_start"]
            ).days

            if 0 <= lag_days <= MAX_LAG_DAYS:
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
                        "start_lag_days": lag_days,
                    }
                )

    return pd.DataFrame(rows)


def summarize_lags(
    matches: pd.DataFrame,
    downstream_station: str,
) -> None:
    """Print lag distribution for one station pair."""
    print(
        f"\n{UPSTREAM_STATION} -> "
        f"{downstream_station}"
    )
    print("=" * 60)

    if matches.empty:
        print("No downstream episodes within the window.")
        return

    counts = (
        matches["start_lag_days"]
        .value_counts()
        .sort_index()
    )

    print(
        "Candidate downstream episodes by "
        "upstream/downstream start-date separation:"
    )

    for lag in range(
        MAX_LAG_DAYS + 1
    ):
        count = counts.get(
            lag,
            0,
        )

        print(
            f"  {lag:2d} days: {count}"
        )

    print(
        f"\nTotal candidate pairs: "
        f"{len(matches)}"
    )

    print(
        f"Median start-date separation: "
        f"{matches['start_lag_days'].median():.1f} days"
    )


def inspect_early_matches(
    matches: pd.DataFrame,
    downstream_station: str,
) -> None:
    """Print earliest candidate matches for manual inspection."""
    print(
        f"\nFirst candidate pairs: "
        f"{UPSTREAM_STATION} -> "
        f"{downstream_station}"
    )
    print("-" * 60)

    if matches.empty:
        print("No matches.")
        return

    preview = matches.sort_values(
        [
            "upstream_start",
            "start_lag_days",
        ]
    ).head(15)

    for _, row in preview.iterrows():
        print(
            f"{row['upstream_start'].date()} "
            f"-> "
            f"{row['downstream_start'].date()} "
            f"({row['start_lag_days']} days)"
        )


def main() -> None:
    """Analyze candidate upstream/downstream episode lags."""
    episodes = load_episodes()

    print(
        f"Loaded {len(episodes)} rise episodes."
    )

    print(
        f"Upstream station: "
        f"{UPSTREAM_STATION}"
    )

    print(
        f"Candidate lag window: "
        f"0-{MAX_LAG_DAYS} days"
    )

    for downstream_station in DOWNSTREAM_STATIONS:
        matches = analyze_pair(
            episodes,
            downstream_station,
        )

        summarize_lags(
            matches,
            downstream_station,
        )

        inspect_early_matches(
            matches,
            downstream_station,
        )


if __name__ == "__main__":
    main()