import csv
from datetime import date, timedelta
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

EXPECTED_COLUMNS = [
    "station_id",
    "date",
    "parameter",
    "water_level_m",
    "quality_symbol",
]

EXPECTED_PARAMETER = "water level/niveau"
EXPECTED_SYMBOLS = {"", "A", "E"}


def processed_path(station_id: str) -> Path:
    """Return the processed daily file for one station."""
    return (
        PROCESSED_DAILY_DIR
        / station_id
        / f"{station_id}_daily_20110101_20241231.csv"
    )


def inspect_station(station_id: str) -> None:
    """Inspect one processed daily dataset."""
    path = processed_path(station_id)

    dates = []
    quality_counts = {"": 0, "A": 0, "E": 0}
    duplicate_dates = set()

    invalid_dates = []
    invalid_values = []
    invalid_rows = []
    unexpected_station_ids = []
    unexpected_parameters = []
    unexpected_symbols = []
    out_of_range_dates = []

    minimum_value = None
    maximum_value = None

    with path.open("r", encoding="utf-8", newline="") as file:
        reader = csv.DictReader(file)

        if reader.fieldnames != EXPECTED_COLUMNS:
            raise ValueError(
                f"{path}: unexpected columns: {reader.fieldnames}"
            )

        seen_dates = set()

        for row_number, row in enumerate(reader, start=2):
            if None in row:
                invalid_rows.append(row_number)
                continue

            station_value = row["station_id"].strip()
            date_text = row["date"].strip()
            parameter = row["parameter"].strip()
            value_text = row["water_level_m"].strip()
            quality_symbol = row["quality_symbol"].strip()

            if station_value != station_id:
                unexpected_station_ids.append(
                    (row_number, station_value)
                )

            if parameter != EXPECTED_PARAMETER:
                unexpected_parameters.append(
                    (row_number, parameter)
                )

            if quality_symbol not in EXPECTED_SYMBOLS:
                unexpected_symbols.append(
                    (row_number, quality_symbol)
                )

            try:
                observation_date = date.fromisoformat(date_text)
            except ValueError:
                invalid_dates.append((row_number, date_text))
                continue

            if not (
                EXPECTED_START
                <= observation_date
                <= EXPECTED_END
            ):
                out_of_range_dates.append(
                    (row_number, date_text)
                )

            if observation_date in seen_dates:
                duplicate_dates.add(observation_date)

            seen_dates.add(observation_date)
            dates.append(observation_date)

            try:
                water_level = float(value_text)
            except ValueError:
                invalid_values.append(
                    (row_number, value_text)
                )
                continue

            if water_level != water_level:
                invalid_values.append(
                    (row_number, value_text)
                )
                continue

            if minimum_value is None or water_level < minimum_value:
                minimum_value = water_level

            if maximum_value is None or water_level > maximum_value:
                maximum_value = water_level

            quality_counts[quality_symbol] += 1

    missing_dates = []

    if dates:
        first_date = min(dates)
        last_date = max(dates)

        expected_date = first_date

        date_set = set(dates)

        while expected_date <= last_date:
            if expected_date not in date_set:
                missing_dates.append(expected_date)

            expected_date += timedelta(days=1)

    dates_are_sorted = dates == sorted(dates)

    print("\n" + "=" * 70)
    print(f"Station: {station_id}")
    print(f"File: {path}")

    print("\nCoverage:")
    print(f"  Rows: {len(dates)}")
    print(f"  First date: {min(dates) if dates else None}")
    print(f"  Last date: {max(dates) if dates else None}")
    print(f"  Expected start: {EXPECTED_START}")
    print(f"  Expected end: {EXPECTED_END}")

    print("\nOrdering and duplicates:")
    print(f"  Dates in chronological order: {dates_are_sorted}")
    print(f"  Duplicate dates: {len(duplicate_dates)}")

    print("\nGaps:")
    print(f"  Missing dates between first and last: {len(missing_dates)}")

    if missing_dates:
        print("  First missing dates:")
        for missing_date in missing_dates[:10]:
            print(f"    {missing_date}")

    print("\nQuality symbols:")
    print(f"  Blank: {quality_counts['']}")
    print(f"  A: {quality_counts['A']}")
    print(f"  E: {quality_counts['E']}")

    print("\nValues:")
    print(f"  Minimum water level: {minimum_value}")
    print(f"  Maximum water level: {maximum_value}")

    print("\nValidation errors:")
    print(f"  Invalid dates: {len(invalid_dates)}")
    print(f"  Out-of-range dates: {len(out_of_range_dates)}")
    print(f"  Invalid water levels: {len(invalid_values)}")
    print(f"  Invalid CSV rows: {len(invalid_rows)}")
    print(f"  Unexpected station IDs: {len(unexpected_station_ids)}")
    print(f"  Unexpected parameters: {len(unexpected_parameters)}")
    print(f"  Unexpected symbols: {len(unexpected_symbols)}")

    if not dates_are_sorted:
        raise ValueError(
            f"{station_id}: processed dates are not chronological."
        )

    if duplicate_dates:
        raise ValueError(
            f"{station_id}: duplicate dates found: "
            f"{sorted(duplicate_dates)[:5]}"
        )

    if invalid_dates:
        raise ValueError(
            f"{station_id}: invalid dates found."
        )

    if out_of_range_dates:
        raise ValueError(
            f"{station_id}: dates outside expected range found."
        )

    if invalid_values:
        raise ValueError(
            f"{station_id}: invalid water-level values found."
        )

    if invalid_rows:
        raise ValueError(
            f"{station_id}: malformed CSV rows found."
        )

    if unexpected_station_ids:
        raise ValueError(
            f"{station_id}: unexpected station IDs found."
        )

    if unexpected_parameters:
        raise ValueError(
            f"{station_id}: unexpected parameters found."
        )

    if unexpected_symbols:
        raise ValueError(
            f"{station_id}: unexpected quality symbols found."
        )

    print("\nResult: PASS")


def main() -> None:
    """Inspect all processed daily datasets."""
    for station_id in STATIONS:
        inspect_station(station_id)

    print("\n" + "=" * 70)
    print("All processed daily validation checks passed.")


if __name__ == "__main__":
    main()
