from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd


INPUT_PATH = Path("data/processed/events/matched_rise_episodes.csv")
OUTPUT_PATH = Path("reports/figures/historical_association_outcomes.png")


def main():
    df = pd.read_csv(INPUT_PATH)

    if df.empty:
        raise ValueError("No historical association records found.")

    outcome_counts = (
        df.groupby(["downstream_station_id", "match_status"])
        .size()
        .unstack(fill_value=0)
        .sort_index()
    )

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)

    outcome_counts.plot(
        kind="bar",
        stacked=True,
        figsize=(9, 5),
        edgecolor="black",
    )

    plt.xlabel("Downstream station")
    plt.ylabel("Number of historical upstream episodes")
    plt.title("Historical Association Outcomes by Downstream Station")
    plt.legend(title="Match status")
    plt.tight_layout()
    plt.savefig(OUTPUT_PATH, dpi=150)
    plt.close()

    print(f"Stations plotted: {len(outcome_counts)}")
    print(f"Records plotted: {len(df)}")
    print(f"Output: {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
