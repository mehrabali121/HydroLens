from pathlib import Path

import pandas as pd


EVENT_PATH = Path(
    "data/processed/events/detected_rise_events.csv"
)

OUTPUT_PATH = Path(
    "data/processed/events/rise_episodes.csv"
)

STATIONS = [
    "01AF002",
    "01AK003",
    "01AO012",
    "01AP003",
]

# Allow one non-trigger day between significant-rise triggers.
MAX_NON_TRIGGER_DAYS = 1


def load_events() -> pd.DataFrame:
    """Load detected significant-rise triggers."""
    if not EVENT_PATH.exists():
        raise FileNotFoundError(
            f"Event file does not exist: {EVENT_PATH}"
        )

    dataframe = pd.read_csv(EVENT_PATH)

    dataframe["trigger_date"] = pd.to_datetime(
        dataframe["trigger_date"]
    )

    return dataframe.sort_values(
        ["station_id", "trigger_date"]
    ).reset_index(drop=True)


def group_station_events(
    station_events: pd.DataFrame,
) -> pd.DataFrame:
    """
    Assign significant-rise triggers to episodes.

    Triggers remain in the same episode when the gap between
    consecutive trigger dates is no more than two calendar days.
    This allows one non-trigger day between triggers.
    """
    result = station_events.copy()

    result["trigger_gap_days"] = (
        result["trigger_date"]
        .diff()
        .dt.days
    )

    maximum_trigger_gap = (
        MAX_NON_TRIGGER_DAYS + 1
    )

    result["new_episode"] = (
        result["trigger_gap_days"].isna()
        | (
            result["trigger_gap_days"]
            > maximum_trigger_gap
        )
    )

    result["episode_number"] = (
        result["new_episode"]
        .cumsum()
    )

    return result


def build_episode_records(
    events: pd.DataFrame,
    stations: list[str] = STATIONS,
) -> pd.DataFrame:
    """Build one record for each station-level rise episode."""
    episodes = []

    for station_id in stations:
        station_events = events[
            events["station_id"] == station_id
        ].copy()

        grouped = group_station_events(
            station_events
        )

        for (
            episode_number,
            episode_events,
        ) in grouped.groupby(
            "episode_number",
            sort=True,
        ):
            first_event = episode_events.iloc[0]

            last_event = episode_events.iloc[-1]

            largest_event = episode_events.loc[
                episode_events["trigger_rise_m"].idxmax()
            ]

            episode_start = (
                episode_events["trigger_date"].min()
            )

            episode_end = (
                episode_events["trigger_date"].max()
            )

            duration_days = (
                episode_end - episode_start
            ).days + 1

            episode_id = (
                f"{station_id}_"
                f"{episode_start.strftime('%Y%m%d')}"
            )

            episodes.append(
                {
                    "episode_id": episode_id,
                    "station_id": station_id,
                    "episode_start": episode_start,
                    "episode_end": episode_end,
                    "duration_days": duration_days,
                    "trigger_count": len(
                        episode_events
                    ),
                    "first_trigger_date": (
                        first_event["trigger_date"]
                    ),
                    "last_trigger_date": (
                        last_event["trigger_date"]
                    ),
                    "largest_trigger_date": (
                        largest_event["trigger_date"]
                    ),
                    "largest_trigger_rise_m": (
                        largest_event["trigger_rise_m"]
                    ),
                }
            )

    return pd.DataFrame(episodes)


def validate_episodes(
    events: pd.DataFrame,
    episodes: pd.DataFrame,
) -> None:
    """Validate basic episode construction."""
    if episodes.empty:
        raise ValueError(
            "No rise episodes were created."
        )

    if episodes["episode_id"].duplicated().any():
        raise ValueError(
            "Duplicate episode IDs detected."
        )

    if (
        episodes["trigger_count"].sum()
        != len(events)
    ):
        raise ValueError(
            "Episode trigger counts do not add up "
            "to the number of detected triggers."
        )

    if (
        episodes["duration_days"] < 1
    ).any():
        raise ValueError(
            "An episode has an invalid duration."
        )

    if (
        episodes["episode_start"]
        > episodes["episode_end"]
    ).any():
        raise ValueError(
            "An episode starts after it ends."
        )


def save_episodes(
    episodes: pd.DataFrame,
) -> None:
    """Save rise episodes to CSV."""
    OUTPUT_PATH.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    episodes.to_csv(
        OUTPUT_PATH,
        index=False,
    )


def show_summary(
    episodes: pd.DataFrame,
) -> None:
    """Print episode summary by station."""
    print("Rise episode summary")
    print("=" * 60)

    for station_id in STATIONS:
        station = episodes[
            episodes["station_id"] == station_id
        ]

        print(
            f"{station_id}: "
            f"{len(station)} episodes, "
            f"{station['trigger_count'].sum()} triggers, "
            f"median duration "
            f"{station['duration_days'].median():.1f} d, "
            f"maximum duration "
            f"{station['duration_days'].max()} d"
        )

    print(
        f"\nTotal episodes: {len(episodes)}"
    )

    print(
        f"Total triggers represented: "
        f"{episodes['trigger_count'].sum()}"
    )


def show_longest_episodes(
    episodes: pd.DataFrame,
) -> None:
    """Print the longest episodes."""
    print("\nLongest episodes")
    print("=" * 60)

    for station_id in STATIONS:
        station = episodes[
            episodes["station_id"] == station_id
        ]

        longest = station.nlargest(
            5,
            "duration_days",
        )

        print(f"\n{station_id}")

        for _, row in longest.iterrows():
            print(
                f"  {row['episode_start'].date()} "
                f"to "
                f"{row['episode_end'].date()} | "
                f"{row['duration_days']} d | "
                f"{row['trigger_count']} triggers | "
                f"largest +"
                f"{row['largest_trigger_rise_m']:.3f} m"
            )


def main() -> None:
    """Build historical rise episodes from detected triggers."""
    events = load_events()

    episodes = build_episode_records(
        events
    )

    validate_episodes(
        events,
        episodes,
    )

    save_episodes(
        episodes
    )

    show_summary(
        episodes
    )

    show_longest_episodes(
        episodes
    )

    print(
        f"\nSaved rise episodes to: "
        f"{OUTPUT_PATH}"
    )


if __name__ == "__main__":
    main()