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

DAILY_DIRECTORY = (
    PROJECT_ROOT
    / "data"
    / "processed"
    / "daily"
)

OUTPUT_DIRECTORY = (
    PROJECT_ROOT
    / "data"
    / "processed"
    / "events"
)

OUTPUT_FILE = (
    OUTPUT_DIRECTORY
    / "match_data_availability.csv"
)

MATCH_WINDOW_DAYS = 2

UPSTREAM_STATION = "01AF002"

DOWNSTREAM_STATIONS = [
    "01AK003",
    "01AO012",
    "01AP003",
]


def load_matches() -> pd.DataFrame:
    """Load and validate the historical episode matches."""
    if not MATCH_FILE.exists():
        raise FileNotFoundError(
            f"Match file not found: {MATCH_FILE}"
        )

    matches = pd.read_csv(MATCH_FILE)

    required_columns = {
        "match_id",
        "upstream_episode_id",
        "upstream_station_id",
        "upstream_start_date",
        "upstream_end_date",
        "downstream_station_id",
        "downstream_episode_id",
        "match_status",
        "target_downstream_station",
    }

    missing_columns = required_columns - set(matches.columns)

    if missing_columns:
        raise ValueError(
            "Missing required match columns: "
            + ", ".join(sorted(missing_columns))
        )

    matches["upstream_start_date"] = pd.to_datetime(
        matches["upstream_start_date"]
    )

    matches["upstream_end_date"] = pd.to_datetime(
        matches["upstream_end_date"]
    )

    if not matches["match_id"].is_unique:
        raise ValueError(
            "Match IDs are not unique."
        )

    if not (
        matches["upstream_station_id"] == UPSTREAM_STATION
    ).all():
        raise ValueError(
            "Unexpected upstream station in match file."
        )

    return matches


def load_daily_station_data(
    station_id: str,
) -> pd.DataFrame:
    """Load cleaned daily observations for one station."""
    station_file = (
        DAILY_DIRECTORY
        / station_id
        / f"{station_id}_daily_20110101_20241231.csv"
    )

    if not station_file.exists():
        raise FileNotFoundError(
            f"Processed daily file not found: {station_file}"
        )

    df = pd.read_csv(station_file)

    required_columns = {
        "station_id",
        "date",
        "parameter",
        "water_level_m",
        "quality_symbol",
    }

    missing_columns = required_columns - set(df.columns)

    if missing_columns:
        raise ValueError(
            f"{station_id}: missing required columns: "
            + ", ".join(sorted(missing_columns))
        )

    df["date"] = pd.to_datetime(df["date"])

    if not (df["station_id"] == station_id).all():
        raise ValueError(
            f"{station_id}: station ID mismatch in daily data."
        )

    if df["date"].duplicated().any():
        raise ValueError(
            f"{station_id}: duplicate daily dates found."
        )

    return df.sort_values("date").reset_index(drop=True)


def build_station_date_index(
    station_id: str,
) -> set:
    """Return the set of dates with stored daily observations."""
    daily = load_daily_station_data(station_id)

    return set(daily["date"].dt.normalize())


def evaluate_window(
    upstream_start_date: pd.Timestamp,
    downstream_dates: set,
) -> tuple:
    """
    Evaluate the daily observations required to determine
    whether a downstream rise could have started from the
    upstream start date through two days afterward.

    The day before the upstream start is included because
    the rise detector requires a previous valid daily
    observation to calculate the change.
    """
    window_start = (
        upstream_start_date
        - pd.Timedelta(days=1)
    )

    window_end = (
        upstream_start_date
        + pd.Timedelta(days=MATCH_WINDOW_DAYS)
    )

    expected_dates = pd.date_range(
        start=window_start,
        end=window_end,
        freq="D",
    )

    available_dates = [
        date
        for date in expected_dates
        if date in downstream_dates
    ]

    missing_dates = [
        date
        for date in expected_dates
        if date not in downstream_dates
    ]

    return (
        expected_dates,
        available_dates,
        missing_dates,
    )


def classify_availability(
    match_status: str,
    missing_dates: list,
) -> str:
    """
    Classify whether the downstream episode matching result
    can be evaluated from available daily observations.
    """
    if match_status == "matched":
        return "matched"

    if not missing_dates:
        return "evaluable_no_candidate"

    return "insufficient_data"


def build_availability_records(
    matches: pd.DataFrame,
    station_dates: dict,
) -> pd.DataFrame:
    """Build one data-availability record per match."""
    records = []

    for _, row in matches.iterrows():
        downstream_station = row["target_downstream_station"]

        (
            expected_dates,
            available_dates,
            missing_dates,
        ) = evaluate_window(
            row["upstream_start_date"],
            station_dates[downstream_station],
        )

        availability_status = classify_availability(
            row["match_status"],
            missing_dates,
        )

        records.append(
            {
                "match_id": row["match_id"],
                "upstream_episode_id": (
                    row["upstream_episode_id"]
                ),
                "upstream_station_id": (
                    row["upstream_station_id"]
                ),
                "upstream_start_date": (
                    row["upstream_start_date"].strftime(
                        "%Y-%m-%d"
                    )
                ),
                "target_downstream_station": (
                    downstream_station
                ),
                "original_match_status": (
                    row["match_status"]
                ),
                "required_window_start": (
                    expected_dates[0].strftime(
                        "%Y-%m-%d"
                    )
                ),
                "required_window_end": (
                    expected_dates[-1].strftime(
                        "%Y-%m-%d"
                    )
                ),
                "expected_observation_days": (
                    len(expected_dates)
                ),
                "available_observation_days": (
                    len(available_dates)
                ),
                "missing_observation_days": (
                    len(missing_dates)
                ),
                "missing_dates": (
                    ";".join(
                        date.strftime("%Y-%m-%d")
                        for date in missing_dates
                    )
                ),
                "availability_status": (
                    availability_status
                ),
            }
        )

    return pd.DataFrame(records)


def validate_output(
    availability: pd.DataFrame,
) -> None:
    """Validate the generated data-availability output."""
    if availability.empty:
        raise ValueError(
            "Availability output is empty."
        )

    if not availability["match_id"].is_unique:
        raise ValueError(
            "Availability match IDs are not unique."
        )

    expected_days = MATCH_WINDOW_DAYS + 2

    if not (
        availability["expected_observation_days"]
        == expected_days
    ).all():
        raise ValueError(
            "Unexpected number of expected observation days."
        )

    if not (
        availability["available_observation_days"]
        + availability["missing_observation_days"]
        == expected_days
    ).all():
        raise ValueError(
            "Available + missing observation counts do not "
            "equal the expected window size."
        )

    valid_statuses = {
        "matched",
        "evaluable_no_candidate",
        "insufficient_data",
    }

    unexpected_statuses = set(
        availability["availability_status"]
    ) - valid_statuses

    if unexpected_statuses:
        raise ValueError(
            "Unexpected availability statuses: "
            + ", ".join(sorted(unexpected_statuses))
        )


def print_summary(
    availability: pd.DataFrame,
) -> None:
    """Print the availability evaluation summary."""
    print()
    print("=" * 90)
    print("DOWNSTREAM DATA AVAILABILITY SUMMARY")
    print("=" * 90)

    print(
        "Required data window: one day before upstream start "
        f"through {MATCH_WINDOW_DAYS} days afterward"
    )

    print()

    for station in DOWNSTREAM_STATIONS:
        station_data = availability[
            availability["target_downstream_station"]
            == station
        ]

        print(f"{UPSTREAM_STATION} -> {station}")
        print(
            "  Total upstream episodes evaluated: "
            f"{len(station_data)}"
        )

        status_counts = (
            station_data["availability_status"]
            .value_counts()
            .sort_index()
        )

        for status in [
            "matched",
            "evaluable_no_candidate",
            "insufficient_data",
        ]:
            print(
                f"  {status}: "
                f"{status_counts.get(status, 0)}"
            )

        print(
            "  Missing-date windows: "
            f"{(station_data['missing_observation_days'] > 0).sum()}"
        )

        print()

    print(
        "Important: insufficient_data means the downstream "
        "response cannot be fairly evaluated from the available "
        "daily observations."
    )


def main() -> None:
    """Evaluate downstream data availability for all matches."""
    print("Loading historical episode matches...")

    matches = load_matches()

    print(f"Match file: {MATCH_FILE}")
    print(f"Total match records: {len(matches)}")

    print()
    print("Loading downstream daily observation dates...")

    station_dates = {}

    for station in DOWNSTREAM_STATIONS:
        station_dates[station] = (
            build_station_date_index(station)
        )

        print(
            f"  {station}: "
            f"{len(station_dates[station])} observation dates"
        )

    availability = build_availability_records(
        matches,
        station_dates,
    )

    validate_output(
        availability,
    )

    OUTPUT_DIRECTORY.mkdir(
        parents=True,
        exist_ok=True,
    )

    availability.to_csv(
        OUTPUT_FILE,
        index=False,
    )

    print()
    print(
        "Availability output written to:"
    )
    print(OUTPUT_FILE)

    print_summary(
        availability,
    )

    print()
    print("Validation passed.")


if __name__ == "__main__":
    main()