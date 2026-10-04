from pathlib import Path

import pandas as pd


INPUT_PATH = Path("data/processed/events/matched_rise_episodes.csv")
OUTPUT_PATH = Path("data/processed/events/historical_backtest_results.csv")


def main():
    df = pd.read_csv(INPUT_PATH)

    matched = df[df["match_status"] == "matched"].copy()

    if matched.empty:
        raise ValueError("No matched historical associations found.")

    matched["upstream_start_date"] = pd.to_datetime(
        matched["upstream_start_date"]
    )
    matched["downstream_start_date"] = pd.to_datetime(
        matched["downstream_start_date"]
    )

    matched["observed_lag_days"] = (
        matched["downstream_start_date"]
        - matched["upstream_start_date"]
    ).dt.days

    if not matched["observed_lag_days"].isin([0, 1, 2]).all():
        raise ValueError(
            "Observed lag falls outside the historical matching window."
        )

    matched["within_historical_window"] = matched["observed_lag_days"].between(
        0, 2
    )

    if not matched["within_historical_window"].all():
        raise ValueError("Backtest contains an association outside the allowed window.")

    result = matched[
        [
            "match_id",
            "upstream_episode_id",
            "upstream_station_id",
            "upstream_start_date",
            "downstream_episode_id",
            "downstream_station_id",
            "downstream_start_date",
            "observed_lag_days",
            "relationship",
            "within_historical_window",
        ]
    ].copy()

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    result.to_csv(OUTPUT_PATH, index=False)

    print(f"Matched historical associations: {len(result)}")
    print(
        "Within historical matching window:",
        int(result["within_historical_window"].sum()),
    )
    print("\nObserved lag distribution:")
    print(result["observed_lag_days"].value_counts().sort_index())
    print(f"\nOutput: {OUTPUT_PATH}")


if __name__ == "__main__":
    main()