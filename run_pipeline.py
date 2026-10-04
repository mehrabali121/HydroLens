"""Run the full HydroLens pipeline in order.

Usage (from the project folder):
    python run_pipeline.py
"""

import subprocess
import sys
from pathlib import Path


RAW_DAILY_DIR = Path("data/raw/daily")

STATIONS = ["01AF002", "01AK003", "01AO012", "01AP003"]

PIPELINE_STEPS = [
    "scripts/clean_daily.py",
    "scripts/create_database.py",
    "scripts/load_daily_database.py",
    "scripts/detect_rise_events.py",
    "scripts/build_rise_episodes.py",
    "scripts/match_rise_episodes.py",
    "scripts/evaluate_match_data_availability.py",
    "scripts/inspect_unmatched_windows.py",
    "scripts/classify_historical_associations.py",
    "scripts/analyze_lead_times.py",
    "scripts/plot_lead_time_distribution.py",
    "scripts/plot_lead_time_by_station.py",
    "scripts/plot_historical_association_outcomes.py",
    "scripts/export_results.py",
]


def check_raw_data() -> None:
    """Stop early if the raw WSC downloads are missing."""
    missing = []

    for station_id in STATIONS:
        raw_file = (
            RAW_DAILY_DIR
            / station_id
            / f"wsc_{station_id}_daily_20110101_20241231.csv"
        )

        if not raw_file.exists():
            missing.append(station_id)

    if missing:
        print("Missing raw data for:", ", ".join(missing))
        print("Download each one first, for example:")
        print(
            "  python scripts/acquire_wsc.py "
            "--station 01AF002 --start 2011-01-01 --end 2024-12-31"
        )
        sys.exit(1)


def main() -> None:
    check_raw_data()

    for step in PIPELINE_STEPS:
        print(f"\n=== Running {step} ===")

        result = subprocess.run([sys.executable, step])

        if result.returncode != 0:
            print(f"\nPipeline stopped: {step} failed.")
            sys.exit(result.returncode)

    print("\nPipeline finished successfully.")


if __name__ == "__main__":
    main()