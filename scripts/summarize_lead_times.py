from pathlib import Path

import pandas as pd


INPUT_PATH = Path("data/processed/events/historical_lead_times.csv")


def main():
    df = pd.read_csv(INPUT_PATH)

    print("Historical Lead-Time Summary")
    print("============================")
    print(f"Matched records: {len(df)}")

    print("\nOverall:")
    print(f"Mean: {df['lead_time_days'].mean():.3f} days")
    print(f"Median: {df['lead_time_days'].median():.3f} days")
    print(f"Minimum: {df['lead_time_days'].min()} days")
    print(f"Maximum: {df['lead_time_days'].max()} days")
    print(f"Standard deviation: {df['lead_time_days'].std():.3f} days")

    q1 = df["lead_time_days"].quantile(0.25)
    q3 = df["lead_time_days"].quantile(0.75)

    print(f"Q1: {q1:.3f} days")
    print(f"Q3: {q3:.3f} days")
    print(f"IQR: {q3 - q1:.3f} days")

    print("\nDistribution:")
    print(df["lead_time_days"].value_counts().sort_index())

    print("\nBy downstream station:")
    summary = df.groupby("downstream_station_id")["lead_time_days"].agg(
        ["count", "mean", "median", "std", "min", "max"]
    )
    print(summary)

    print("\nCoverage:")
    print("Overall historical records: 177")
    print(f"Matched lead-time records: {len(df)}")
    print(f"Lead-time coverage: {len(df) / 177 * 100:.1f}%")

    print("\nInterpretation constraint:")
    print(
        "Lead-time statistics describe matched historical associations only; "
        "unmatched and insufficient cases do not receive a lead-time value."
    )


if __name__ == "__main__":
    main()