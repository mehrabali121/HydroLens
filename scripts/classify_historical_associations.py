from pathlib import Path

import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[1]

MATCH_FILE = PROJECT_ROOT / "data" / "processed" / "events" / "matched_rise_episodes.csv"
AVAILABILITY_FILE = (
    PROJECT_ROOT
    / "data"
    / "processed"
    / "events"
    / "match_data_availability.csv"
)
UNMATCHED_ANALYSIS_FILE = (
    PROJECT_ROOT
    / "data"
    / "processed"
    / "events"
    / "unmatched_window_analysis.csv"
)

OUTPUT_FILE = (
    PROJECT_ROOT
    / "data"
    / "processed"
    / "events"
    / "historical_association_summary.csv"
)


EXPECTED_MATCH_COLUMNS = {
    "match_id",
    "upstream_station_id",
    "target_downstream_station",
    "match_status",
    "start_lag_days",
}

EXPECTED_AVAILABILITY_COLUMNS = {
    "match_id",
    "upstream_station_id",
    "target_downstream_station",
    "availability_status",
}

EXPECTED_UNMATCHED_COLUMNS = {
    "match_id",
    "window_result",
}


def load_inputs() -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """Load and validate the three Phase 10 analysis outputs."""
    for path in (MATCH_FILE, AVAILABILITY_FILE, UNMATCHED_ANALYSIS_FILE):
        if not path.exists():
            raise FileNotFoundError(f"Required file not found: {path}")

    matches = pd.read_csv(MATCH_FILE)
    availability = pd.read_csv(AVAILABILITY_FILE)
    unmatched_analysis = pd.read_csv(UNMATCHED_ANALYSIS_FILE)

    missing_matches = EXPECTED_MATCH_COLUMNS - set(matches.columns)
    if missing_matches:
        raise ValueError(
            f"Missing required match columns: {sorted(missing_matches)}"
        )

    missing_availability = EXPECTED_AVAILABILITY_COLUMNS - set(
        availability.columns
    )
    if missing_availability:
        raise ValueError(
            "Missing required availability columns: "
            f"{sorted(missing_availability)}"
        )

    missing_unmatched = EXPECTED_UNMATCHED_COLUMNS - set(
        unmatched_analysis.columns
    )
    if missing_unmatched:
        raise ValueError(
            "Missing required unmatched-analysis columns: "
            f"{sorted(missing_unmatched)}"
        )

    return matches, availability, unmatched_analysis


def classify_records(
    matches: pd.DataFrame,
    availability: pd.DataFrame,
    unmatched_analysis: pd.DataFrame,
) -> pd.DataFrame:
    """Assign one final historical association class to every match record."""

    availability_subset = availability[
        [
            "match_id",
            "availability_status",
        ]
    ].copy()

    unmatched_subset = unmatched_analysis[
        [
            "match_id",
            "window_result",
        ]
    ].copy()

    if availability_subset["match_id"].duplicated().any():
        raise ValueError("Duplicate match IDs found in availability data.")

    if unmatched_subset["match_id"].duplicated().any():
        raise ValueError(
            "Duplicate match IDs found in unmatched-window analysis."
        )

    result = matches.merge(
        availability_subset,
        on="match_id",
        how="left",
        validate="one_to_one",
    )

    result = result.merge(
        unmatched_subset,
        on="match_id",
        how="left",
        validate="one_to_one",
    )

    if result["availability_status"].isna().any():
        raise ValueError(
            "Some match records do not have a corresponding availability "
            "classification."
        )

    def determine_class(row: pd.Series) -> str:
        if row["match_status"] == "matched":
            return "matched"

        if row["availability_status"] == "insufficient_data":
            return "insufficient_data"

        if row["window_result"] == "significant_rise_during_existing_episode":
            return "pre_existing_episode"

        if row["availability_status"] == "evaluable_no_candidate":
            return "no_candidate"

        raise ValueError(
            "Could not classify match record "
            f"{row['match_id']!r}: "
            f"match_status={row['match_status']!r}, "
            f"availability_status={row['availability_status']!r}, "
            f"window_result={row['window_result']!r}"
        )

    result["association_class"] = result.apply(determine_class, axis=1)

    return result


def summarize_by_pair(classified: pd.DataFrame) -> pd.DataFrame:
    """Create one summary row for each upstream/downstream station pair."""

    rows = []

    for (upstream_station, downstream_station), group in classified.groupby(
        ["upstream_station_id", "target_downstream_station"],
        sort=True,
    ):
        matched = int((group["association_class"] == "matched").sum())

        pre_existing = int(
            (group["association_class"] == "pre_existing_episode").sum()
        )

        no_candidate = int(
            (group["association_class"] == "no_candidate").sum()
        )

        insufficient = int(
            (group["association_class"] == "insufficient_data").sum()
        )

        total = len(group)

        primary_match_evaluable = matched + no_candidate

        broader_association_evaluable = (
            matched + pre_existing + no_candidate
        )

        directional_match_proportion = (
            matched / primary_match_evaluable
            if primary_match_evaluable
            else float("nan")
        )

        broader_temporal_association_proportion = (
            (matched + pre_existing) / broader_association_evaluable
            if broader_association_evaluable
            else float("nan")
        )

        matched_group = group[
            group["association_class"] == "matched"
        ]

        same_day = int(
            (matched_group["start_lag_days"] == 0).sum()
        )

        one_day = int(
            (matched_group["start_lag_days"] == 1).sum()
        )

        two_day = int(
            (matched_group["start_lag_days"] == 2).sum()
        )

        positive_lags = matched_group.loc[
            matched_group["start_lag_days"] > 0,
            "start_lag_days",
        ]

        median_positive_start_separation = (
            float(positive_lags.median())
            if not positive_lags.empty
            else float("nan")
        )

        rows.append(
            {
                "upstream_station_id": upstream_station,
                "downstream_station_id": downstream_station,
                "total_upstream_episodes": total,
                "matched_episodes": matched,
                "pre_existing_episodes": pre_existing,
                "no_candidate_episodes": no_candidate,
                "insufficient_data": insufficient,
                "primary_match_evaluable": primary_match_evaluable,
                "broader_association_evaluable": broader_association_evaluable,
                "directional_match_proportion": directional_match_proportion,
                "broader_temporal_association_proportion": (
                    broader_temporal_association_proportion
                ),
                "same_day_matches": same_day,
                "one_day_matches": one_day,
                "two_day_matches": two_day,
                "median_positive_start_separation_days": (
                    median_positive_start_separation
                ),
            }
        )

    return pd.DataFrame(rows)


def validate_classification(
    classified: pd.DataFrame,
    summary: pd.DataFrame,
) -> None:
    """Validate classification counts and reporting consistency."""

    expected_classes = {
        "matched",
        "pre_existing_episode",
        "no_candidate",
        "insufficient_data",
    }

    actual_classes = set(
        classified["association_class"].unique()
    )

    unexpected_classes = actual_classes - expected_classes

    if unexpected_classes:
        raise ValueError(
            f"Unexpected association classes: {sorted(unexpected_classes)}"
        )

    if classified["match_id"].duplicated().any():
        raise ValueError(
            "Duplicate match IDs found after classification."
        )

    expected_record_count = (
        classified["upstream_episode_id"].nunique() * 3
    )

    if len(classified) != expected_record_count:
        raise ValueError(
            f"Expected {expected_record_count} classified records, "
            f"found {len(classified)}."
        )

    if len(summary) != 3:
        raise ValueError(
            f"Expected 3 station-pair summaries, found {len(summary)}."
        )

    # Every upstream episode must land in exactly one class for
    # each downstream station, so no record is lost or counted twice.
    for _, row in summary.iterrows():
        class_total = (
            row["matched_episodes"]
            + row["pre_existing_episodes"]
            + row["no_candidate_episodes"]
            + row["insufficient_data"]
        )

        if class_total != row["total_upstream_episodes"]:
            raise ValueError(
                f"Class counts for {row['downstream_station_id']} "
                f"add up to {class_total}, expected "
                f"{row['total_upstream_episodes']}."
            )

    for column in [
        "directional_match_proportion",
        "broader_temporal_association_proportion",
    ]:
        if not summary[column].between(0, 1).all():
            raise ValueError(f"{column} has values outside 0 to 1.")


def print_summary(summary: pd.DataFrame) -> None:
    """Print a readable station-pair summary."""

    print("\nHistorical association summary")
    print("=" * 80)

    for _, row in summary.iterrows():
        print(
            f"\n{row['upstream_station_id']} -> "
            f"{row['downstream_station_id']}"
        )

        print(
            f"  Total upstream episodes:        "
            f"{int(row['total_upstream_episodes'])}"
        )

        print(
            f"  Matched:                        "
            f"{int(row['matched_episodes'])}"
        )

        print(
            f"  Pre-existing downstream:       "
            f"{int(row['pre_existing_episodes'])}"
        )

        print(
            f"  No candidate:                  "
            f"{int(row['no_candidate_episodes'])}"
        )

        print(
            f"  Insufficient data:              "
            f"{int(row['insufficient_data'])}"
        )

        print(
            f"  Directional match evaluable:   "
            f"{int(row['primary_match_evaluable'])}"
        )

        print(
            f"  Directional match proportion:  "
            f"{row['directional_match_proportion']:.1%}"
        )

        print(
            f"  Broader association evaluable: "
            f"{int(row['broader_association_evaluable'])}"
        )

        print(
            f"  Broader temporal association:  "
            f"{row['broader_temporal_association_proportion']:.1%}"
        )

        print(
            f"  Same-day matches:               "
            f"{int(row['same_day_matches'])}"
        )

        print(
            f"  1-day matches:                  "
            f"{int(row['one_day_matches'])}"
        )

        print(
            f"  2-day matches:                  "
            f"{int(row['two_day_matches'])}"
        )

        print(
            f"  Median positive separation:     "
            f"{row['median_positive_start_separation_days']:.1f} days"
        )


def main() -> None:
    matches, availability, unmatched_analysis = load_inputs()

    classified = classify_records(
        matches,
        availability,
        unmatched_analysis,
    )

    summary = summarize_by_pair(classified)

    validate_classification(
        classified,
        summary,
    )

    OUTPUT_FILE.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    summary.to_csv(
        OUTPUT_FILE,
        index=False,
    )

    print(f"Classified records: {len(classified)}")
    print(f"Output: {OUTPUT_FILE}")

    print_summary(summary)

    print("\nValidation passed.")


if __name__ == "__main__":
    main()