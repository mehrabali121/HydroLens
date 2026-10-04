from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd


INPUT_PATH = Path("data/processed/events/historical_lead_times.csv")
OUTPUT_PATH = Path("reports/figures/historical_lead_time_distribution.png")


def main():
    df = pd.read_csv(INPUT_PATH)

    if df.empty:
        raise ValueError("No historical lead-time records found.")

    lead_times = df["lead_time_days"].dropna()

    if lead_times.empty:
        raise ValueError("No valid lead-time values found.")

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)

    plt.figure(figsize=(8, 5))
    plt.hist(
        lead_times,
        bins=[-0.5, 0.5, 1.5, 2.5],
        edgecolor="black",
    )
    plt.xticks([0, 1, 2])
    plt.xlabel("Lead time (days)")
    plt.ylabel("Number of matched historical associations")
    plt.title("Historical Lead-Time Distribution")
    plt.tight_layout()
    plt.savefig(OUTPUT_PATH, dpi=150)
    plt.close()

    print(f"Records plotted: {len(lead_times)}")
    print(f"Output: {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
