import csv
from datetime import date
from pathlib import Path

PROCESSED_DAILY_DIR = Path("data/processed/daily")

STATIONS = [
    "01AF002",
    "01AK003",
    "01AO012",
    "01AP003",
]

EXPECTED_START = date(2011, 1, 1)
EXPECTED_END = date(2024, 12, 31)


def processed_path(station_id: str) -> Path:
    """Return the processed daily file for one station."""
    return (
        PROCESSED_DAILY_DIR
        / station_id
        / f"{station_id}_daily_20110101_20241231.csv"
    )


def expected_day_count() -> int:
    """Return the number of calendar days in the analysis period."""
    return (EXPECTED_END - EXPECTED_START).days + 1


def summarize_station(station_id: str) -> dict[str, object]:
    """Summarize one processed daily dataset."""
    path = processed_path(station_id)

    dates = []
    quality_counts = {
        "": 0,
        "A": 0,
        "E": 0,
    }

    minimum_value = None
    maximum_value = None

    with path.open("r", encoding="utf-8", newline="") as file:
        reader = csv.DictReader(file)

        for row in reader:
            observation_date = date.fromisoformat(
                row["date"].strip()
            )
            water_level = float(row["water_level_m"].strip())
            quality_symbol = row["quality_symbol"].strip()

            dates.append(observation_date)
            quality_counts[quality_symbol] += 1

            if minimum_value is None or water_level < minimum_value:
                minimum_value = water_level

            if maximum_value is None or water_level > maximum_value:
                maximum_value = water_level

    observed_days = len(set(dates))
    expected_days = expected_day_count()
    missing_days = expected_days - observed_days
    coverage_percentage = (
        observed_days / expected_days
    ) * 100

    return {
        "station_id": station_id,
        "observed_days": observed_days,
        "expected_days": expected_days,
        "missing_days": missing_days,
        "coverage_percentage": coverage_percentage,
        "first_date": min(dates),
        "last_date": max(dates),
        "blank_quality": quality_counts[""],
        "partial_day": quality_counts["A"],
        "estimated": quality_counts["E"],
        "minimum_value": minimum_value,
        "maximum_value": maximum_value,
    }


def main() -> None:
    """Summarize all processed daily datasets."""
    summaries = []

    for station_id in STATIONS:
        summaries.append(summarize_station(station_id))

    print("=" * 100)
    print("PROCESSED DAILY DATA COVERAGE SUMMARY")
    print("=" * 100)

    print(
        f"\nAnalysis period: "
        f"{EXPECTED_START} to {EXPECTED_END}"
    )

    print(f"Expected calendar days: {expected_day_count()}")

    for summary in summaries:
        print("\n" + "-" * 100)
        print(f"Station: {summary['station_id']}")

        print(
            f"  Observed days: "
            f"{summary['observed_days']} / "
            f"{summary['expected_days']}"
        )

        print(
            f"  Missing days: "
            f"{summary['missing_days']}"
        )

        print(
            f"  Coverage: "
            f"{summary['coverage_percentage']:.2f}%"
        )

        print(
            f"  First observation: "
            f"{summary['first_date']}"
        )

        print(
            f"  Last observation: "
            f"{summary['last_date']}"
        )

        print("  Quality:")
        print(
            f"    Blank: "
            f"{summary['blank_quality']}"
        )
        print(
            f"    A (partial day): "
            f"{summary['partial_day']}"
        )
        print(
            f"    E (estimated): "
            f"{summary['estimated']}"
        )

        print("  Water-level range:")
        print(
            f"    Minimum: "
            f"{summary['minimum_value']:.3f} m"
        )
        print(
            f"    Maximum: "
            f"{summary['maximum_value']:.3f} m"
        )

    print("\n" + "=" * 100)
    print("Summary complete.")


if __name__ == "__main__":
    main()