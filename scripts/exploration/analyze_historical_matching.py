from pathlib import Path

import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[2]

MATCH_FILE = (
    PROJECT_ROOT
    / "data"
    / "processed"
    / "events"
    / "matched_rise_episodes.csv"
)

AVAILABILITY_FILE = (
    PROJECT_ROOT
    / "data"
    / "processed"
    / "events"
    / "match_data_availability.csv"
)

OUTPUT_DIRECTORY = (
    PROJECT_ROOT
    / "data"
    / "processed"
    / "events"
)

OUTPUT_FILE = (
    OUTPUT_DIRECTORY
    / "historical_matching_summary.csv"
)

UPSTREAM_STATION = "01AF002"

DOWNSTREAM_STATIONS = [
    "01AK003",
    "01AO012",
    "01AP003",
]


def load_data() -> tuple[pd.DataFrame, pd.DataFrame]:
    """Load and validate matching and availability data."""
    if not MATCH_FILE.exists():
        raise FileNotFoundError(
            f"Match file not found: {MATCH_FILE}"
        )

    if not AVAILABILITY_FILE.exists():
        raise FileNotFoundError(
            f"Availability file not found: {AVAILABILITY_FILE}"
        )

    matches = pd.read_csv(MATCH_FILE)
    availability = pd.read_csv(AVAILABILITY_FILE)

    required_match_columns = {
        "match_id",
        "upstream_episode_id",
        "upstream_station_id",
        "target_downstream_station",
        "downstream_episode_id",
        "start_lag_days",
        "match_status",
    }

    required_availability_columns = {
        "match_id",
        "target_downstream_station",
        "availability_status",
    }

    missing_match = (
        required_match_columns - set(matches.columns)
    )

    missing_availability = (
        required_availability_columns
        - set(availability.columns)
    )

    if missing_match:
        raise ValueError(
            "Missing match columns: "
            + ", ".join(sorted(missing_match))
        )

    if missing_availability:
        raise ValueError(
            "Missing availability columns: "
            + ", ".join(sorted(missing_availability))
        )

    if not matches["match_id"].is_unique:
        raise ValueError(
            "Match IDs are not unique."
        )

    if not availability["match_id"].is_unique:
        raise ValueError(
            "Availability match IDs are not unique."
        )

    if not (
        matches["upstream_station_id"] == UPSTREAM_STATION
    ).all():
        raise ValueError(
            "Unexpected upstream station found."
        )

    return matches, availability


def build_summary(
    matches: pd.DataFrame,
    availability: pd.DataFrame,
) -> pd.DataFrame:
    """Build station-level historical matching statistics."""
    merged = matches.merge(
        availability[
            [
                "match_id",
                "availability_status",
            ]
        ],
        on="match_id",
        how="inner",
        validate="one_to_one",
    )

    records = []

    for station in DOWNSTREAM_STATIONS:
        station_data = merged[
            merged["target_downstream_station"] == station
        ].copy()

        total_episodes = len(station_data)

        matched = station_data[
            station_data["availability_status"] == "matched"
        ]

        evaluable_no_candidate = station_data[
            station_data["availability_status"]
            == "evaluable_no_candidate"
        ]

        insufficient_data = station_data[
            station_data["availability_status"]
            == "insufficient_data"
        ]

        matched_count = len(matched)
        evaluable_count = len(evaluable_no_candidate)
        insufficient_count = len(insufficient_data)

        evaluable_total = (
            matched_count + evaluable_count
        )

        if evaluable_total == 0:
            matched_proportion = None
        else:
            matched_proportion = (
                matched_count / evaluable_total
            )

        lag_counts = (
            matched["start_lag_days"]
            .value_counts()
            .to_dict()
        )

        if matched_count > 0:
            median_lag = (
                matched["start_lag_days"].median()
            )
        else:
            median_lag = None

        records.append(
            {
                "upstream_station_id": UPSTREAM_STATION,
                "downstream_station_id": station,
                "total_upstream_episodes": total_episodes,
                "matched_episodes": matched_count,
                "evaluable_no_candidate": evaluable_count,
                "insufficient_data": insufficient_count,
                "evaluable_episodes": evaluable_total,
                "historical_matched_proportion": (
                    matched_proportion
                ),
                "same_day_matches": lag_counts.get(
                    0, 0
                ),
                "one_day_matches": lag_counts.get(
                    1, 0
                ),
                "two_day_matches": lag_counts.get(
                    2, 0
                ),
                "median_start_separation_days": (
                    median_lag
                ),
            }
        )

    return pd.DataFrame(records)


def validate_summary(
    summary: pd.DataFrame,
) -> None:
    """Validate station-level matching statistics."""
    if len(summary) != len(DOWNSTREAM_STATIONS):
        raise ValueError(
            "Unexpected number of downstream stations."
        )

    if not summary["downstream_station_id"].is_unique:
        raise ValueError(
            "Duplicate downstream stations in summary."
        )

    for _, row in summary.iterrows():
        total = row["total_upstream_episodes"]

        if (
            row["matched_episodes"]
            + row["evaluable_no_candidate"]
            + row["insufficient_data"]
            != total
        ):
            raise ValueError(
                "Episode categories do not sum to total "
                f"for {row['downstream_station_id']}."
            )

        if (
            row["matched_episodes"]
            != row["same_day_matches"]
            + row["one_day_matches"]
            + row["two_day_matches"]
        ):
            raise ValueError(
                "Lag categories do not sum to matched "
                f"episodes for {row['downstream_station_id']}."
            )

        if not (
            0.0
            <= row["historical_matched_proportion"]
            <= 1.0
        ):
            raise ValueError(
                "Matched proportion outside [0, 1] for "
                f"{row['downstream_station_id']}."
            )


def print_summary(
    summary: pd.DataFrame,
) -> None:
    """Print the historical matching summary."""
    print()
    print("=" * 90)
    print("HISTORICAL EPISODE MATCHING ANALYSIS")
    print("=" * 90)

    print(
        "Primary matching rule: downstream episode starts "
        "0–2 days after upstream episode start"
    )

    print(
        "Matched proportion denominator: matched + "
        "evaluable no-candidate episodes"
    )

    print()

    for _, row in summary.iterrows():
        station = row["downstream_station_id"]

        proportion = (
            row["historical_matched_proportion"] * 100
        )

        print(
            f"{UPSTREAM_STATION} -> {station}"
        )
        print(
            "  Total upstream episodes: "
            f"{row['total_upstream_episodes']}"
        )
        print(
            "  Matched episodes: "
            f"{row['matched_episodes']}"
        )
        print(
            "  Evaluable no-candidate episodes: "
            f"{row['evaluable_no_candidate']}"
        )
        print(
            "  Insufficient-data episodes: "
            f"{row['insufficient_data']}"
        )
        print(
            "  Evaluable episodes: "
            f"{row['evaluable_episodes']}"
        )
        print(
            "  Historical matched-episode proportion: "
            f"{proportion:.1f}%"
        )
        print(
            "  Same-day matches: "
            f"{row['same_day_matches']}"
        )
        print(
            "  1-day matches: "
            f"{row['one_day_matches']}"
        )
        print(
            "  2-day matches: "
            f"{row['two_day_matches']}"
        )
        print(
            "  Median start separation: "
            f"{row['median_start_separation_days']:.1f} days"
        )
        print()


def main() -> None:
    """Calculate historical matching statistics."""
    print("Loading historical matching data...")

    matches, availability = load_data()

    print(f"Match records: {len(matches)}")
    print(f"Availability records: {len(availability)}")

    summary = build_summary(
        matches,
        availability,
    )

    validate_summary(summary)

    OUTPUT_DIRECTORY.mkdir(
        parents=True,
        exist_ok=True,
    )

    summary.to_csv(
        OUTPUT_FILE,
        index=False,
    )

    print()
    print(
        "Summary written to:"
    )
    print(OUTPUT_FILE)

    print_summary(summary)

    print("Validation passed.")


if __name__ == "__main__":
    main()