import csv
from collections import Counter
from datetime import date, timedelta
from pathlib import Path


RAW_DAILY_DIR = Path("data/raw/daily")

FILES = {
    "01AF002": (
        RAW_DAILY_DIR
        / "01AF002"
        / "wsc_01AF002_daily_20110101_20241231.csv"
    ),
    "01AK003": (
        RAW_DAILY_DIR
        / "01AK003"
        / "wsc_01AK003_daily_20110101_20241231.csv"
    ),
    "01AO012": (
        RAW_DAILY_DIR
        / "01AO012"
        / "wsc_01AO012_daily_20110101_20241231.csv"
    ),
    "01AP003": (
        RAW_DAILY_DIR
        / "01AP003"
        / "wsc_01AP003_daily_20110101_20241231.csv"
    ),
}

COMMON_START = date(2011, 1, 1)
COMMON_END = date(2024, 12, 31)


def read_dates(path: Path) -> tuple[list[date], set[date]]:
    """Read daily observation dates and detect duplicates."""

    dates = []
    seen_dates = set()
    duplicate_dates = set()

    with path.open("r", encoding="utf-8-sig", newline="") as file:
        reader = csv.DictReader(file)

        for row in reader:
            observation_date = date.fromisoformat(row["Date"])

            if observation_date in seen_dates:
                duplicate_dates.add(observation_date)

            seen_dates.add(observation_date)
            dates.append(observation_date)

    return dates, duplicate_dates


def inspect_station(station_id: str, path: Path) -> set[date]:
    """Print basic date coverage information for one WSC station."""

    dates, duplicate_dates = read_dates(path)
    sorted_dates = sorted(dates)

    if not sorted_dates:
        print(f"{station_id}: no data")
        return set()

    gaps = []

    for previous, current in zip(sorted_dates, sorted_dates[1:]):
        gap_days = (current - previous).days

        if gap_days > 1:
            gaps.append((previous, current, gap_days - 1))

    print(f"\nStation: {station_id}")
    print(f"Rows: {len(dates)}")
    print(f"Unique dates: {len(set(dates))}")
    print(f"First date: {sorted_dates[0]}")
    print(f"Last date: {sorted_dates[-1]}")
    print(f"Duplicate dates: {len(duplicate_dates)}")

    if duplicate_dates:
        print(
            "Duplicate date values: "
            + ", ".join(
                str(observation_date)
                for observation_date in sorted(duplicate_dates)
            )
        )

    if gaps:
        largest_gap = max(gaps, key=lambda item: item[2])

        print(f"Number of gaps: {len(gaps)}")
        print(
            "Largest gap: "
            f"{largest_gap[2]} missing days "
            f"between {largest_gap[0]} and {largest_gap[1]}"
        )
    else:
        print("Number of gaps: 0")
        print("Largest gap: none")

    return set(dates)


def inspect_common_coverage(
    station_dates: dict[str, set[date]],
) -> None:
    """Measure station availability across the common date range."""

    availability_counts = Counter()
    missing_station_counts = Counter()

    current = COMMON_START

    while current <= COMMON_END:
        available_stations = {
            station_id
            for station_id, dates in station_dates.items()
            if current in dates
        }

        availability_counts[len(available_stations)] += 1

        missing_stations = set(station_dates) - available_stations

        if missing_stations:
            missing_station_counts[
                tuple(sorted(missing_stations))
            ] += 1

        current += timedelta(days=1)

    total_days = (COMMON_END - COMMON_START).days + 1

    print("\nCommon analysis window")
    print(f"Start: {COMMON_START}")
    print(f"End: {COMMON_END}")
    print(f"Total calendar days: {total_days}")

    for station_count in range(4, -1, -1):
        days = availability_counts[station_count]
        percentage = days / total_days * 100

        print(
            f"Days with {station_count}/4 stations available: "
            f"{days} ({percentage:.2f}%)"
        )

    print("\nMissing station combinations")

    for missing_stations, days in sorted(
        missing_station_counts.items(),
        key=lambda item: (-item[1], item[0]),
    ):
        print(
            f"Missing {', '.join(missing_stations)}: "
            f"{days} days"
        )


def inspect_three_station_runs(
    station_dates: dict[str, set[date]],
) -> None:
    """Find continuous runs where exactly one station is missing."""

    runs = []

    current = COMMON_START
    active_missing = None
    run_start = None
    previous_date = None

    while current <= COMMON_END:
        available_stations = {
            station_id
            for station_id, dates in station_dates.items()
            if current in dates
        }

        missing_stations = set(station_dates) - available_stations

        if len(missing_stations) == 1:
            missing_station = next(iter(missing_stations))

            if (
                active_missing == missing_station
                and previous_date is not None
                and current == previous_date + timedelta(days=1)
            ):
                pass
            else:
                if active_missing is not None:
                    runs.append(
                        (
                            active_missing,
                            run_start,
                            previous_date,
                        )
                    )

                active_missing = missing_station
                run_start = current

            previous_date = current

        else:
            if active_missing is not None:
                runs.append(
                    (
                        active_missing,
                        run_start,
                        previous_date,
                    )
                )

            active_missing = None
            run_start = None
            previous_date = None

        current += timedelta(days=1)

    if active_missing is not None:
        runs.append(
            (
                active_missing,
                run_start,
                previous_date,
            )
        )

    print("\nLongest continuous periods with exactly one station missing")

    runs.sort(
        key=lambda item: (item[2] - item[1]).days,
        reverse=True,
    )

    for station_id, start, end in runs[:10]:
        duration = (end - start).days + 1

        print(
            f"Missing {station_id}: "
            f"{start} to {end} "
            f"({duration} days)"
        )


def main() -> None:
    station_dates = {}

    for station_id, path in FILES.items():
        station_dates[station_id] = inspect_station(
            station_id,
            path,
        )

    inspect_common_coverage(station_dates)
    inspect_three_station_runs(station_dates)


if __name__ == "__main__":
    main()