from pathlib import Path

import pandas as pd


INPUT_PATH = Path("data/processed/events/historical_backtest_results.csv")


def main():
    df = pd.read_csv(INPUT_PATH)

    total = len(df)
    within_window = int(df["within_historical_window"].sum())
    outside_window = total - within_window

    print("Historical Backtest Summary")
    print("===========================")
    print(f"Matched historical associations: {total}")
    print(f"Within historical window: {within_window}")
    print(f"Outside historical window: {outside_window}")
    print(f"Within-window rate: {within_window / total * 100:.1f}%")

    print("\nObserved lag distribution:")
    print(df["observed_lag_days"].value_counts().sort_index())

    print("\nBy downstream station:")
    summary = df.groupby("downstream_station_id")["observed_lag_days"].agg(
        ["count", "mean", "median", "min", "max"]
    )
    print(summary)

    if outside_window != 0:
        raise ValueError("Backtest contains associations outside the historical window.")


if __name__ == "__main__":
    main()