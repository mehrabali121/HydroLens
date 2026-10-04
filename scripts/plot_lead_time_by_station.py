from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd


INPUT_PATH = Path("data/processed/events/historical_lead_times.csv")
OUTPUT_PATH = Path("reports/figures/lead_time_by_downstream_station.png")


def main():
    df = pd.read_csv(INPUT_PATH)

    if df.empty:
        raise ValueError("No historical lead-time records found.")

    summary = (
        df.groupby("downstream_station_id")["lead_time_days"]
        .mean()
        .sort_index()
    )

    if summary.empty:
        raise ValueError("No station-level lead-time data found.")

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)

    plt.figure(figsize=(8, 5))
    plt.bar(
        summary.index,
        summary.values,
        edgecolor="black",
    )
    plt.xlabel("Downstream station")
    plt.ylabel("Mean lead time (days)")
    plt.title("Mean Historical Lead Time by Downstream Station")
    plt.tight_layout()
    plt.savefig(OUTPUT_PATH, dpi=150)
    plt.close()

    print(f"Stations plotted: {len(summary)}")
    print(f"Output: {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
