from pathlib import Path

import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[1]

EPISODE_FILE = (
    PROJECT_ROOT
    / "data"
    / "processed"
    / "events"
    / "rise_episodes.csv"
)

OUTPUT_DIRECTORY = (
    PROJECT_ROOT
    / "data"
    / "processed"
    / "events"
)

MATCHED_OUTPUT_FILE = (
    OUTPUT_DIRECTORY
    / "matched_rise_episodes.csv"
)

UPSTREAM_STATION = "01AF002"

DOWNSTREAM_STATIONS = [
    "01AK003",
    "01AO012",
    "01AP003",
]

MATCH_WINDOW_DAYS = 2


def load_episodes() -> pd.DataFrame:
    """Load and validate historical rise episodes."""
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

    date_columns = [
        "episode_start",
        "episode_end",
        "first_trigger_date",
        "last_trigger_date",
        "largest_trigger_date",
    ]

    for column in date_columns:
        df[column] = pd.to_datetime(df[column])

    if not df["episode_id"].is_unique:
        raise ValueError("Episode IDs are not unique.")

    if not (df["episode_start"] == df["first_trigger_date"]).all():
        raise ValueError(
            "Some episode_start values do not match first_trigger_date."
        )

    if not (df["episode_end"] >= df["episode_start"]).all():
        raise ValueError(
            "At least one episode ends before it starts."
        )

    return df


def prepare_station_columns(
    df: pd.DataFrame,
    prefix: str,
) -> pd.DataFrame:
    """Rename episode columns for upstream/downstream matching."""
    return df.rename(
        columns={
            "episode_id": f"{prefix}_episode_id",
            "station_id": f"{prefix}_station_id",
            "episode_start": f"{prefix}_start_date",
            "episode_end": f"{prefix}_end_date",
            "duration_days": f"{prefix}_duration_days",
            "trigger_count": f"{prefix}_trigger_count",
            "largest_trigger_date": f"{prefix}_largest_rise_date",
            "largest_trigger_rise_m": f"{prefix}_largest_rise_m",
        }
    )


def find_candidates(
    upstream: pd.DataFrame,
    downstream: pd.DataFrame,
) -> pd.DataFrame:
    """Find downstream episodes within the primary 0–2 day window."""
    upstream = prepare_station_columns(
        upstream,
        "upstream",
    )

    downstream = prepare_station_columns(
        downstream,
        "downstream",
    )

    merged = upstream.merge(
        downstream,
        how="cross",
    )

    merged["start_lag_days"] = (
        merged["downstream_start_date"]
        - merged["upstream_start_date"]
    ).dt.days

    candidates = merged[
        merged["start_lag_days"].between(
            0,
            MATCH_WINDOW_DAYS,
        )
    ].copy()

    candidates["relationship"] = candidates.apply(
        classify_relationship,
        axis=1,
    )

    return candidates


def classify_relationship(row: pd.Series) -> str:
    """Classify the temporal relationship between two episodes."""
    if row["downstream_start_date"] <= row["upstream_end_date"]:
        return "overlap"

    return "follow_up"


def select_nearest_candidates(
    candidates: pd.DataFrame,
) -> pd.DataFrame:
    """Select the nearest downstream candidate for each upstream episode."""
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
        .groupby(
            "upstream_episode_id",
            as_index=False,
        )
        .first()
    )

    return selected


def build_match_records(
    upstream: pd.DataFrame,
    selected: pd.DataFrame,
    downstream_station: str,
) -> pd.DataFrame:
    """
    Create one record for every upstream episode.

    Matched episodes receive their selected downstream episode.
    Episodes without a candidate are retained with no downstream
    episode so they are not incorrectly treated as failures.
    """
    base_columns = [
        "episode_id",
        "station_id",
        "episode_start",
        "episode_end",
        "duration_days",
        "trigger_count",
        "largest_trigger_date",
        "largest_trigger_rise_m",
    ]

    upstream_base = upstream[base_columns].copy()

    upstream_base = upstream_base.rename(
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

    selected_columns = [
        "upstream_episode_id",
        "downstream_episode_id",
        "downstream_station_id",
        "downstream_start_date",
        "downstream_end_date",
        "downstream_duration_days",
        "downstream_trigger_count",
        "downstream_largest_rise_date",
        "downstream_largest_rise_m",
        "start_lag_days",
        "relationship",
    ]

    selected = selected[selected_columns].copy()

    matches = upstream_base.merge(
        selected,
        how="left",
        on="upstream_episode_id",
    )

    matches["target_downstream_station"] = downstream_station

    matches["match_status"] = matches["downstream_episode_id"].apply(
        lambda value: (
            "matched"
            if pd.notna(value)
            else "no_candidate_within_window"
        )
    )

    matches["match_window_days"] = MATCH_WINDOW_DAYS

    matches["match_id"] = matches.apply(
        lambda row: (
            f"{row['upstream_episode_id']}"
            f"__{downstream_station}"
            if row["match_status"] == "matched"
            else (
                f"{row['upstream_episode_id']}"
                f"__{downstream_station}"
                f"__unmatched"
            )
        ),
        axis=1,
    )

    return matches


def validate_matches(
    matches: pd.DataFrame,
    downstream_station: str,
) -> None:
    """Validate the generated historical match records."""
    if matches.empty:
        raise ValueError(
            f"No upstream records produced for {downstream_station}."
        )

    if not matches["match_id"].is_unique:
        raise ValueError(
            f"Duplicate match IDs found for {downstream_station}."
        )

    if not (
        matches["upstream_station_id"] == UPSTREAM_STATION
    ).all():
        raise ValueError(
            "Unexpected upstream station in match output."
        )

    if not (
        matches["target_downstream_station"]
        == downstream_station
    ).all():
        raise ValueError(
            "Unexpected target downstream station."
        )

    matched = matches[
        matches["match_status"] == "matched"
    ].copy()

    if not matched.empty:
        if not matched["downstream_episode_id"].is_unique:
            raise ValueError(
                f"A downstream episode was reused for "
                f"{downstream_station}."
            )

        if not matched["start_lag_days"].between(
            0,
            MATCH_WINDOW_DAYS,
        ).all():
            raise ValueError(
                "A matched episode falls outside the matching window."
            )

        if matched["downstream_station_id"].ne(
            downstream_station
        ).any():
            raise ValueError(
                "Unexpected downstream station in matched records."
            )

    unmatched = matches[
        matches["match_status"] == "no_candidate_within_window"
    ]

    if not unmatched["downstream_episode_id"].isna().all():
        raise ValueError(
            "Unmatched records contain downstream episode IDs."
        )


def analyze_station_pair(
    episodes: pd.DataFrame,
    downstream_station: str,
) -> pd.DataFrame:
    """Match Grand Falls episodes against one downstream station."""
    upstream = episodes[
        episodes["station_id"] == UPSTREAM_STATION
    ].copy()

    downstream = episodes[
        episodes["station_id"] == downstream_station
    ].copy()

    if upstream.empty:
        raise ValueError(
            f"No episodes found for {UPSTREAM_STATION}."
        )

    if downstream.empty:
        raise ValueError(
            f"No episodes found for {downstream_station}."
        )

    candidates = find_candidates(
        upstream,
        downstream,
    )

    selected = select_nearest_candidates(
        candidates,
    )

    matches = build_match_records(
        upstream,
        selected,
        downstream_station,
    )

    validate_matches(
        matches,
        downstream_station,
    )

    return matches


def combine_station_matches(
    episodes: pd.DataFrame,
) -> pd.DataFrame:
    """Build the final match dataset for all downstream stations."""
    results = []

    for downstream_station in DOWNSTREAM_STATIONS:
        matches = analyze_station_pair(
            episodes,
            downstream_station,
        )

        results.append(matches)

    combined = pd.concat(
        results,
        ignore_index=True,
    )

    combined = combined[
        [
            "match_id",
            "upstream_episode_id",
            "upstream_station_id",
            "upstream_start_date",
            "upstream_end_date",
            "upstream_duration_days",
            "upstream_trigger_count",
            "upstream_largest_rise_date",
            "upstream_largest_rise_m",
            "downstream_episode_id",
            "downstream_station_id",
            "downstream_start_date",
            "downstream_end_date",
            "downstream_duration_days",
            "downstream_trigger_count",
            "downstream_largest_rise_date",
            "downstream_largest_rise_m",
            "start_lag_days",
            "relationship",
            "match_status",
            "match_window_days",
            "target_downstream_station",
        ]
    ]

    numeric_columns = [
        "upstream_largest_rise_m",
        "downstream_largest_rise_m",
        "start_lag_days",
        "match_window_days",
    ]

    for column in numeric_columns:
        combined[column] = combined[column].round(3)

    combined = combined.sort_values(
        [
            "target_downstream_station",
            "upstream_start_date",
            "upstream_episode_id",
        ]
    ).reset_index(drop=True)

    return combined


def print_summary(
    matches: pd.DataFrame,
) -> None:
    """Print summary statistics without calculating response success."""
    print()
    print("=" * 90)
    print("HISTORICAL EPISODE MATCHING SUMMARY")
    print("=" * 90)

    print(
        f"Matching rule: downstream episode starts "
        f"0–{MATCH_WINDOW_DAYS} days after upstream episode start"
    )

    print(
        "Selection rule: nearest downstream candidate per "
        "upstream episode"
    )

    print()

    for station in DOWNSTREAM_STATIONS:
        station_matches = matches[
            matches["target_downstream_station"] == station
        ].copy()

        matched = station_matches[
            station_matches["match_status"] == "matched"
        ]

        unmatched = station_matches[
            station_matches["match_status"]
            == "no_candidate_within_window"
        ]

        print(f"{UPSTREAM_STATION} -> {station}")
        print(f"  Upstream episodes: {len(station_matches)}")
        print(f"  Matched: {len(matched)}")
        print(
            "  No candidate within window: "
            f"{len(unmatched)}"
        )

        if not matched.empty:
            print(
                "  Same-day associations: "
                f"{(matched['start_lag_days'] == 0).sum()}"
            )

            print(
                "  1-day associations: "
                f"{(matched['start_lag_days'] == 1).sum()}"
            )

            print(
                "  2-day associations: "
                f"{(matched['start_lag_days'] == 2).sum()}"
            )

            print(
                "  Median start separation: "
                f"{matched['start_lag_days'].median():.1f} days"
            )

            print(
                "  Downstream episodes reused: "
                f"{matched['downstream_episode_id'].duplicated().sum()}"
            )

        print()

    print(
        "Note: 'no_candidate_within_window' is not a failure "
        "classification."
    )

    print(
        "Later analysis must evaluate downstream data availability "
        "before interpreting unmatched episodes."
    )


def main() -> None:
    """Run the reusable historical episode matcher."""
    print("Loading historical rise episodes...")

    episodes = load_episodes()

    print(f"Episode file: {EPISODE_FILE}")
    print(f"Total episodes: {len(episodes)}")

    matches = combine_station_matches(
        episodes,
    )

    OUTPUT_DIRECTORY.mkdir(
        parents=True,
        exist_ok=True,
    )

    matches.to_csv(
        MATCHED_OUTPUT_FILE,
        index=False,
    )

    print()
    print("Match output written to:")
    print(MATCHED_OUTPUT_FILE)

    print_summary(matches)

    print()
    print("Validation passed.")


if __name__ == "__main__":
    main()