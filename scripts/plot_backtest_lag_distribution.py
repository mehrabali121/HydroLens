from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd


INPUT_PATH = Path("data/processed/events/historical_backtest_results.csv")
OUTPUT_PATH = Path("reports/figures/historical_backtest_lag_distribution.png")


def main():
    df = pd.read_csv(INPUT_PATH)

    if df.empty:
        raise ValueError("No historical backtest records found.")

    lag_counts = df["observed_lag_days"].value_counts().sort_index()

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)

    plt.figure(figsize=(8, 5))
    plt.bar(
        lag_counts.index.astype(str),
        lag_counts.values,
        edgecolor="black",
    )
    plt.xlabel("Observed lag (days)")
    plt.ylabel("Number of matched historical associations")
    plt.title("Historical Backtest Lag Distribution")
    plt.tight_layout()
    plt.savefig(OUTPUT_PATH, dpi=150)
    plt.close()

    print(f"Records plotted: {len(df)}")
    print(f"Output: {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
