from pathlib import Path

import numpy as np
import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[1]

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

EPISODE_FILE = (
    PROJECT_ROOT
    / "data"
    / "processed"
    / "events"
    / "rise_episodes.csv"
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
    / "unmatched_window_analysis.csv"
)

UPSTREAM_STATION = "01AF002"

DOWNSTREAM_STATIONS = [
    "01AK003",
    "01AO012",
    "01AP003",
]


def load_matches() -> pd.DataFrame:
    """Load the historical matching output."""
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
        "target_downstream_station",
        "match_status",
    }

    missing = required_columns - set(matches.columns)

    if missing:
        raise ValueError(
            "Missing match columns: "
            + ", ".join(sorted(missing))
        )

    matches["upstream_start_date"] = pd.to_datetime(
        matches["upstream_start_date"]
    )

    return matches


def load_availability() -> pd.DataFrame:
    """Load downstream data-availability classifications."""
    if not AVAILABILITY_FILE.exists():
        raise FileNotFoundError(
            f"Availability file not found: "
            f"{AVAILABILITY_FILE}"
        )

    availability = pd.read_csv(
        AVAILABILITY_FILE
    )

    required_columns = {
        "match_id",
        "target_downstream_station",
        "availability_status",
    }

    missing = (
        required_columns
        - set(availability.columns)
    )

    if missing:
        raise ValueError(
            "Missing availability columns: "
            + ", ".join(sorted(missing))
        )

    return availability


def load_episodes() -> pd.DataFrame:
    """Load historical rise episodes."""
    if not EPISODE_FILE.exists():
        raise FileNotFoundError(
            f"Episode file not found: {EPISODE_FILE}"
        )

    episodes = pd.read_csv(
        EPISODE_FILE
    )

    required_columns = {
        "episode_id",
        "station_id",
        "episode_start",
        "episode_end",
        "largest_trigger_date",
        "largest_trigger_rise_m",
    }

    missing = required_columns - set(
        episodes.columns
    )

    if missing:
        raise ValueError(
            "Missing episode columns: "
            + ", ".join(sorted(missing))
        )

    episodes["episode_start"] = pd.to_datetime(
        episodes["episode_start"]
    )

    episodes["episode_end"] = pd.to_datetime(
        episodes["episode_end"]
    )

    episodes["largest_trigger_date"] = pd.to_datetime(
        episodes["largest_trigger_date"]
    )

    return episodes


def load_daily_data(
    station_id: str,
) -> pd.DataFrame:
    """Load one cleaned downstream daily dataset."""
    path = (
        DAILY_DIRECTORY
        / station_id
        / f"{station_id}_daily_20110101_20241231.csv"
    )

    if not path.exists():
        raise FileNotFoundError(
            f"Daily file not found: {path}"
        )

    daily = pd.read_csv(path)

    required_columns = {
        "station_id",
        "date",
        "water_level_m",
        "quality_symbol",
    }

    missing = required_columns - set(
        daily.columns
    )

    if missing:
        raise ValueError(
            f"{station_id}: missing columns: "
            + ", ".join(sorted(missing))
        )

    daily["date"] = pd.to_datetime(
        daily["date"]
    )

    daily = daily.sort_values(
        "date"
    ).reset_index(drop=True)

    daily["elapsed_days"] = (
        daily["date"].diff().dt.days
    )

    daily["daily_rise_m"] = np.where(
        daily["elapsed_days"] == 1,
        daily["water_level_m"].diff(),
        np.nan,
    )

    return daily


def calculate_threshold(
    daily: pd.DataFrame,
) -> float:
    """Calculate the station-specific 95th percentile threshold."""
    positive_rises = daily.loc[
        daily["daily_rise_m"] > 0,
        "daily_rise_m",
    ].dropna()

    if positive_rises.empty:
        raise ValueError(
            "No positive daily rises available."
        )

    return float(
        positive_rises.quantile(0.95)
    )


def find_active_episode(
    episodes: pd.DataFrame,
    station_id: str,
    start_date: pd.Timestamp,
) -> pd.Series | None:
    """
    Find a downstream episode that was already active
    when the evaluation window began.
    """
    station_episodes = episodes[
        episodes["station_id"] == station_id
    ]

    active = station_episodes[
        (
            station_episodes["episode_start"]
            < start_date
        )
        & (
            station_episodes["episode_end"]
            >= start_date
        )
    ].sort_values(
        [
            "episode_start",
            "episode_id",
        ]
    )

    if active.empty:
        return None

    return active.iloc[0]


def analyze_window(
    daily: pd.DataFrame,
    threshold: float,
    episodes: pd.DataFrame,
    station_id: str,
    start_date: pd.Timestamp,
) -> dict:
    """
    Analyze downstream rises from the upstream episode
    start through two days afterward.
    """
    window_end = (
        start_date
        + pd.Timedelta(days=2)
    )

    window = daily[
        (daily["date"] >= start_date)
        & (daily["date"] <= window_end)
    ].copy()

    if window.empty:
        raise ValueError(
            "No downstream observations in evaluation window."
        )

    valid_rises = window[
        window["daily_rise_m"].notna()
    ].copy()

    active_episode = find_active_episode(
        episodes,
        station_id,
        start_date,
    )

    if valid_rises.empty:
        return {
            "window_observation_days": len(window),
            "valid_rise_days": 0,
            "maximum_daily_rise_m": np.nan,
            "maximum_rise_date": "",
            "threshold_m": threshold,
            "threshold_ratio": np.nan,
            "qualifying_rise_count": 0,
            "active_episode_at_window_start": (
                active_episode is not None
            ),
            "active_episode_id": (
                active_episode["episode_id"]
                if active_episode is not None
                else ""
            ),
            "active_episode_start": (
                active_episode["episode_start"].strftime(
                    "%Y-%m-%d"
                )
                if active_episode is not None
                else ""
            ),
            "active_episode_end": (
                active_episode["episode_end"].strftime(
                    "%Y-%m-%d"
                )
                if active_episode is not None
                else ""
            ),
            "window_result": "no_valid_rise",
            "quality_flags_present": "",
        }

    maximum_row = valid_rises.loc[
        valid_rises["daily_rise_m"].idxmax()
    ]

    qualifying = valid_rises[
        valid_rises["daily_rise_m"]
        >= threshold
    ]

    quality_flags = (
        valid_rises["quality_symbol"]
        .fillna("")
        .astype(str)
    )

    quality_flags = sorted(
        {
            flag
            for flag in quality_flags
            if flag.strip()
        }
    )

    maximum_rise = float(
        maximum_row["daily_rise_m"]
    )

    if len(qualifying) == 0:
        window_result = "no_significant_rise"

    elif active_episode is not None:
        window_result = (
            "significant_rise_during_existing_episode"
        )

    else:
        window_result = (
            "significant_rise_without_active_episode"
        )

    return {
        "window_observation_days": len(window),
        "valid_rise_days": len(valid_rises),
        "maximum_daily_rise_m": maximum_rise,
        "maximum_rise_date": (
            maximum_row["date"].strftime(
                "%Y-%m-%d"
            )
        ),
        "threshold_m": threshold,
        "threshold_ratio": (
            maximum_rise / threshold
            if threshold > 0
            else np.nan
        ),
        "qualifying_rise_count": len(
            qualifying
        ),
        "active_episode_at_window_start": (
            active_episode is not None
        ),
        "active_episode_id": (
            active_episode["episode_id"]
            if active_episode is not None
            else ""
        ),
        "active_episode_start": (
            active_episode["episode_start"].strftime(
                "%Y-%m-%d"
            )
            if active_episode is not None
            else ""
        ),
        "active_episode_end": (
            active_episode["episode_end"].strftime(
                "%Y-%m-%d"
            )
            if active_episode is not None
            else ""
        ),
        "window_result": window_result,
        "quality_flags_present": (
            ";".join(quality_flags)
        ),
    }


def build_analysis() -> pd.DataFrame:
    """Analyze every evaluable unmatched upstream episode."""
    matches = load_matches()
    availability = load_availability()
    episodes = load_episodes()

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

    unmatched = merged[
        (
            merged["match_status"]
            == "no_candidate_within_window"
        )
        & (
            merged["availability_status"]
            == "evaluable_no_candidate"
        )
    ].copy()

    station_data = {}
    thresholds = {}

    for station in DOWNSTREAM_STATIONS:
        daily = load_daily_data(station)

        station_data[station] = daily
        thresholds[station] = calculate_threshold(
            daily
        )

    records = []

    for _, row in unmatched.iterrows():
        station = row[
            "target_downstream_station"
        ]

        result = analyze_window(
            station_data[station],
            thresholds[station],
            episodes,
            station,
            row["upstream_start_date"],
        )

        records.append(
            {
                "match_id": row["match_id"],
                "upstream_episode_id": (
                    row["upstream_episode_id"]
                ),
                "upstream_start_date": (
                    row["upstream_start_date"].strftime(
                        "%Y-%m-%d"
                    )
                ),
                "downstream_station_id": station,
                "window_start_date": (
                    row["upstream_start_date"].strftime(
                        "%Y-%m-%d"
                    )
                ),
                "window_end_date": (
                    (
                        row["upstream_start_date"]
                        + pd.Timedelta(days=2)
                    ).strftime(
                        "%Y-%m-%d"
                    )
                ),
                **result,
            }
        )

    return pd.DataFrame(records)


def validate_output(
    analysis: pd.DataFrame,
) -> None:
    """Validate unmatched-window analysis."""
    if analysis.empty:
        raise ValueError(
            "No evaluable unmatched episodes found."
        )

    if not analysis["match_id"].is_unique:
        raise ValueError(
            "Duplicate match IDs found."
        )

    valid_results = {
        "no_valid_rise",
        "no_significant_rise",
        "significant_rise_during_existing_episode",
    }

    unexpected = set(
        analysis["window_result"]
    ) - valid_results

    if unexpected:
        raise ValueError(
            "Unexpected window result: "
            + ", ".join(sorted(unexpected))
        )

    if (
        analysis["window_observation_days"]
        > 3
    ).any():
        raise ValueError(
            "Evaluation window contains more than "
            "three downstream observation dates."
        )


def print_summary(
    analysis: pd.DataFrame,
) -> None:
    """Print diagnostic statistics."""
    print()
    print("=" * 90)
    print("EVALUABLE UNMATCHED WINDOW ANALYSIS")
    print("=" * 90)

    print(
        "Window: upstream episode start through "
        "2 days afterward"
    )

    print()

    for station in DOWNSTREAM_STATIONS:
        station_data = analysis[
            analysis["downstream_station_id"]
            == station
        ]

        if station_data.empty:
            continue

        threshold = (
            station_data["threshold_m"]
            .iloc[0]
        )

        print(
            f"{UPSTREAM_STATION} -> {station}"
        )
        print(
            "  Evaluable unmatched episodes: "
            f"{len(station_data)}"
        )
        print(
            "  Station threshold: "
            f"{threshold:.3f} m"
        )
        print(
            "  No significant rise: "
            f"{(station_data['window_result'] == 'no_significant_rise').sum()}"
        )
        print(
            "  Significant rise during existing episode: "
            f"{(station_data['window_result'] == 'significant_rise_during_existing_episode').sum()}"
        )
        print(
            "  Significant rise without active episode: "
            f"{(station_data['window_result'] == 'significant_rise_without_active_episode').sum()}"
        )
        print(
            "  Median maximum daily rise: "
            f"{station_data['maximum_daily_rise_m'].median():.3f} m"
        )
        print(
            "  Maximum daily rise in windows: "
            f"{station_data['maximum_daily_rise_m'].max():.3f} m"
        )
        print(
            "  Median threshold ratio: "
            f"{station_data['threshold_ratio'].median():.3f}"
        )
        print()


def main() -> None:
    """Run unmatched-window diagnostic analysis."""
    print(
        "Analyzing evaluable unmatched episodes..."
    )

    analysis = build_analysis()

    validate_output(
        analysis
    )

    OUTPUT_DIRECTORY.mkdir(
        parents=True,
        exist_ok=True,
    )

    analysis.to_csv(
        OUTPUT_FILE,
        index=False,
    )

    print()
    print(
        "Analysis written to:"
    )
    print(OUTPUT_FILE)

    print_summary(
        analysis
    )

    print(
        "Validation passed."
    )


if __name__ == "__main__":
    main()