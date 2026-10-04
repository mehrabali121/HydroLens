from pathlib import Path

import pandas as pd


INPUT_PATH = Path("data/processed/events/matched_rise_episodes.csv")
OUTPUT_PATH = Path("data/processed/events/historical_lead_times.csv")


def calculate_lead_times(df: pd.DataFrame) -> pd.DataFrame:
    """Return one row per matched episode with its lead time in days."""
    matched = df[df["match_status"] == "matched"].copy()

    matched["upstream_start_date"] = pd.to_datetime(
        matched["upstream_start_date"]
    )
    matched["downstream_start_date"] = pd.to_datetime(
        matched["downstream_start_date"]
    )

    matched["lead_time_days"] = (
        matched["downstream_start_date"]
        - matched["upstream_start_date"]
    ).dt.days

    result = matched[
        [
            "match_id",
            "upstream_episode_id",
            "upstream_station_id",
            "upstream_start_date",
            "downstream_episode_id",
            "downstream_station_id",
            "downstream_start_date",
            "lead_time_days",
            "relationship",
        ]
    ].copy()

    if result["lead_time_days"].isna().any():
        raise ValueError("Lead-time calculation produced missing values.")

    if not result["lead_time_days"].isin([0, 1, 2]).all():
        raise ValueError(
            "Lead times fall outside the 0-2 day matching window."
        )

    return result


def main():
    df = pd.read_csv(INPUT_PATH)

    result = calculate_lead_times(df)

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    result.to_csv(OUTPUT_PATH, index=False)

    print(f"Lead-time records: {len(result)}")
    print("\nLead-time counts:")
    print(result["lead_time_days"].value_counts().sort_index())
    print(f"\nOutput: {OUTPUT_PATH}")


if __name__ == "__main__":
    main()