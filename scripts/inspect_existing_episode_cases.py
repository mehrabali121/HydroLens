from pathlib import Path

import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[1]

MATCH_FILE = (
    PROJECT_ROOT
    / "data"
    / "processed"
    / "events"
    / "matched_rise_episodes.csv"
)

ANALYSIS_FILE = (
    PROJECT_ROOT
    / "data"
    / "processed"
    / "events"
    / "unmatched_window_analysis.csv"
)

EPISODE_FILE = (
    PROJECT_ROOT
    / "data"
    / "processed"
    / "events"
    / "rise_episodes.csv"
)


def load_file(
    path: Path,
) -> pd.DataFrame:
    if not path.exists():
        raise FileNotFoundError(
            f"File not found: {path}"
        )

    return pd.read_csv(path)


def main() -> None:
    matches = load_file(MATCH_FILE)
    analysis = load_file(ANALYSIS_FILE)
    episodes = load_file(EPISODE_FILE)

    for column in [
        "upstream_start_date",
        "downstream_start_date",
        "downstream_end_date",
    ]:
        if column in matches.columns:
            matches[column] = pd.to_datetime(
                matches[column]
            )

    for column in [
        "upstream_start_date",
        "active_episode_start",
        "active_episode_end",
    ]:
        if column in analysis.columns:
            analysis[column] = pd.to_datetime(
                analysis[column],
                errors="coerce",
            )

    for column in [
        "episode_start",
        "episode_end",
    ]:
        episodes[column] = pd.to_datetime(
            episodes[column]
        )

    existing_cases = analysis[
        analysis["window_result"]
        == "significant_rise_during_existing_episode"
    ].copy()

    print()
    print("=" * 100)
    print("EXISTING DOWNSTREAM EPISODE CONSISTENCY CHECK")
    print("=" * 100)

    print(
        f"Cases to inspect: {len(existing_cases)}"
    )

    print()

    for _, case in existing_cases.iterrows():
        upstream_episode_id = (
            case["upstream_episode_id"]
        )

        downstream_station = (
            case["downstream_station_id"]
        )

        active_episode_id = (
            case["active_episode_id"]
        )

        upstream_start = pd.Timestamp(
            case["upstream_start_date"]
        )

        print("-" * 100)
        print(
            f"Upstream episode: {upstream_episode_id}"
        )
        print(
            f"Downstream station: {downstream_station}"
        )
        print(
            f"Upstream start: "
            f"{upstream_start.date()}"
        )
        print(
            f"Existing downstream episode: "
            f"{active_episode_id}"
        )
        print(
            f"Existing downstream period: "
            f"{case['active_episode_start'].date()} "
            f"to "
            f"{case['active_episode_end'].date()}"
        )
        print(
            f"Maximum downstream rise in window: "
            f"{case['maximum_daily_rise_m']:.3f} m"
        )
        print(
            f"Downstream threshold: "
            f"{case['threshold_m']:.3f} m"
        )

        matching_rows = matches[
            (
                matches["upstream_episode_id"]
                == upstream_episode_id
            )
            & (
                matches["target_downstream_station"]
                == downstream_station
            )
        ]

        print()
        print(
            "Matching-output record:"
        )

        if matching_rows.empty:
            print(
                "  No record found."
            )
        else:
            for _, match in matching_rows.iterrows():
                print(
                    f"  status = "
                    f"{match['match_status']}"
                )
                print(
                    f"  downstream_episode_id = "
                    f"{match.get('downstream_episode_id', '')}"
                )
                print(
                    f"  downstream_start = "
                    f"{match.get('downstream_start_date', '')}"
                )
                print(
                    f"  downstream_end = "
                    f"{match.get('downstream_end_date', '')}"
                )
                print(
                    f"  start_lag_days = "
                    f"{match.get('start_lag_days', '')}"
                )

        print()
        print(
            "Downstream episode record:"
        )

        episode_rows = episodes[
            (
                episodes["episode_id"]
                == active_episode_id
            )
        ]

        if episode_rows.empty:
            print(
                "  ERROR: episode not found."
            )
        else:
            for _, episode in episode_rows.iterrows():
                print(
                    f"  station = "
                    f"{episode['station_id']}"
                )
                print(
                    f"  start = "
                    f"{episode['episode_start'].date()}"
                )
                print(
                    f"  end = "
                    f"{episode['episode_end'].date()}"
                )
                print(
                    f"  trigger count = "
                    f"{episode['trigger_count']}"
                )
                print(
                    f"  largest rise = "
                    f"{episode['largest_trigger_rise_m']:.3f} m"
                )

        earlier_matches = matches[
            (
                matches["downstream_episode_id"]
                == active_episode_id
            )
            & (
                matches["match_status"]
                == "matched"
            )
        ]

        print()
        print(
            "Other upstream episodes matched "
            "to this downstream episode:"
        )

        if earlier_matches.empty:
            print(
                "  None."
            )
        else:
            for _, match in earlier_matches.iterrows():
                print(
                    f"  {match['upstream_episode_id']} "
                    f"starting "
                    f"{match['upstream_start_date'].date()}"
                )

    print()
    print("=" * 100)
    print("GLOBAL CONSISTENCY CHECKS")
    print("=" * 100)

    matched = matches[
        matches["match_status"] == "matched"
    ]

    print(
        f"Matched records: {len(matched)}"
    )

    print(
        "Unique matched downstream episodes: "
        f"{matched['downstream_episode_id'].nunique()}"
    )

    reused = (
        matched.groupby(
            [
                "target_downstream_station",
                "downstream_episode_id",
            ]
        )
        .size()
        .reset_index(name="count")
    )

    reused = reused[
        reused["count"] > 1
    ]

    print(
        "Downstream episodes reused by multiple "
        f"upstream episodes: {len(reused)}"
    )

    duplicate_upstream = (
        matched.groupby(
            [
                "target_downstream_station",
                "upstream_episode_id",
            ]
        )
        .size()
        .reset_index(name="count")
    )

    duplicate_upstream = duplicate_upstream[
        duplicate_upstream["count"] > 1
    ]

    print(
        "Upstream episodes with multiple matched "
        f"records for the same downstream station: "
        f"{len(duplicate_upstream)}"
    )

    print()
    print(
        "Diagnostic complete."
    )


if __name__ == "__main__":
    main()