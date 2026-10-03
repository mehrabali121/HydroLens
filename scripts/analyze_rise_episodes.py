import pandas as pd
from pathlib import Path


EVENT_PATH = Path(
    "data/processed/events/detected_rise_events.csv"
)

STATIONS = [
    "01AF002",
    "01AK003",
    "01AO012",
    "01AP003",
]

GAP_TOLERANCES = [0, 1, 2]


def load_events() -> pd.DataFrame:
    """Load detected rise triggers."""
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
    gap_tolerance: int,
) -> pd.DataFrame:
    """
    Group trigger dates into episodes.

    A new episode starts when the gap between consecutive
    trigger dates is greater than gap_tolerance + 1 days.
    """
    result = station_events.copy()

    result["trigger_gap_days"] = (
        result["trigger_date"]
        .diff()
        .dt.days
    )

    result["new_episode"] = (
        result["trigger_gap_days"].isna()
        | (
            result["trigger_gap_days"]
            > gap_tolerance + 1
        )
    )

    result["episode_number"] = (
        result["new_episode"]
        .cumsum()
    )

    return result


def build_episodes(
    events: pd.DataFrame,
    gap_tolerance: int,
) -> pd.DataFrame:
    """Build episode-level records for every station."""
    episodes = []

    for station_id in STATIONS:
        station_events = events[
            events["station_id"] == station_id
        ].copy()

        grouped = group_station_events(
            station_events,
            gap_tolerance,
        )

        for (
            episode_number,
            episode_events,
        ) in grouped.groupby(
            "episode_number",
            sort=True,
        ):
            first_event = episode_events.iloc[0]
            peak_event = episode_events.loc[
                episode_events["trigger_rise_m"].idxmax()
            ]

            start_date = episode_events[
                "trigger_date"
            ].min()

            end_date = episode_events[
                "trigger_date"
            ].max()

            episodes.append(
                {
                    "station_id": station_id,
                    "episode_number": int(
                        episode_number
                    ),
                    "episode_start": start_date,
                    "episode_end": end_date,
                    "trigger_count": len(
                        episode_events
                    ),
                    "duration_days": (
                        end_date - start_date
                    ).days
                    + 1,
                    "largest_trigger_rise_m": (
                        peak_event[
                            "trigger_rise_m"
                        ]
                    ),
                    "largest_trigger_date": (
                        peak_event[
                            "trigger_date"
                        ]
                    ),
                    "first_trigger_date": (
                        first_event[
                            "trigger_date"
                        ]
                    ),
                }
            )

    return pd.DataFrame(episodes)


def show_comparison(
    results: dict[int, pd.DataFrame],
) -> None:
    """Show episode counts for each grouping rule."""
    print("Episode grouping sensitivity")
    print("=" * 70)

    print(
        "\nGap tolerance means how many non-trigger days "
        "may occur inside one episode."
    )

    for tolerance, episodes in results.items():
        print(
            f"\nGap tolerance: {tolerance} day(s)"
        )

        for station_id in STATIONS:
            station = episodes[
                episodes["station_id"]
                == station_id
            ]

            multi_trigger = station[
                station["trigger_count"] > 1
            ]

            print(
                f"  {station_id}: "
                f"{len(station)} episodes, "
                f"{len(multi_trigger)} multi-trigger, "
                f"median duration "
                f"{station['duration_days'].median():.1f} d, "
                f"max duration "
                f"{station['duration_days'].max()} d"
            )


def show_merging_effect(
    results: dict[int, pd.DataFrame],
    events: pd.DataFrame,
) -> None:
    """Show how many triggers are contained in multi-trigger episodes."""
    print("\nTrigger merging")
    print("=" * 70)

    for tolerance, episodes in results.items():
        print(
            f"\nGap tolerance: {tolerance} day(s)"
        )

        for station_id in STATIONS:
            station = episodes[
                episodes["station_id"]
                == station_id
            ]

            trigger_count = len(
                events[
                    events["station_id"]
                    == station_id
                ]
            )

            multi_trigger_count = station[
                station["trigger_count"] > 1
            ]["trigger_count"].sum()

            print(
                f"  {station_id}: "
                f"{multi_trigger_count} of "
                f"{trigger_count} triggers "
                f"are inside multi-trigger episodes"
            )


def show_long_episodes(
    results: dict[int, pd.DataFrame],
) -> None:
    """Show the longest episodes under each rule."""
    print("\nLongest episodes")
    print("=" * 70)

    for tolerance, episodes in results.items():
        print(
            f"\nGap tolerance: {tolerance} day(s)"
        )

        for station_id in STATIONS:
            station = episodes[
                episodes["station_id"]
                == station_id
            ]

            longest = station.nlargest(
                5,
                "duration_days",
            )

            print(f"\n  {station_id}")

            for _, row in longest.iterrows():
                print(
                    f"    "
                    f"{row['episode_start'].date()} "
                    f"to "
                    f"{row['episode_end'].date()} | "
                    f"{row['duration_days']} d | "
                    f"{row['trigger_count']} triggers | "
                    f"largest +"
                    f"{row['largest_trigger_rise_m']:.3f} m"
                )


def main() -> None:
    """Run episode grouping sensitivity analysis."""
    events = load_events()

    results = {}

    for tolerance in GAP_TOLERANCES:
        results[tolerance] = build_episodes(
            events,
            tolerance,
        )

    show_comparison(results)
    show_merging_effect(
        results,
        events,
    )
    show_long_episodes(results)


if __name__ == "__main__":
    main()