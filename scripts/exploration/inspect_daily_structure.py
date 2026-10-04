import csv
import math
from collections import Counter
from datetime import date
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

EXPECTED_START = date(2011, 1, 1)
EXPECTED_END = date(2024, 12, 31)

EXPECTED_PARAMETER = "water level/niveau"
EXPECTED_SYMBOLS = {"", "A", "E"}


def inspect_file(station_id: str, path: Path) -> None:
    """Inspect raw daily rows for cleaning-related issues."""

    parameter_counts = Counter()
    symbol_counts = Counter()
    station_id_counts = Counter()

    missing_value_rows = []
    invalid_value_rows = []
    invalid_date_rows = []
    unexpected_station_rows = []
    unexpected_parameter_rows = []
    unexpected_symbol_rows = []
    whitespace_rows = []
    malformed_rows = []

    row_count = 0
    minimum_value = None
    maximum_value = None

    with path.open(
        "r",
        encoding="utf-8-sig",
        newline="",
    ) as file:
        reader = csv.DictReader(file)

        original_columns = reader.fieldnames or []
        normalized_columns = [
            column.strip() for column in original_columns
        ]

        print(f"\n{'=' * 70}")
        print(f"Station: {station_id}")
        print(f"File: {path}")
        print(f"Original columns: {original_columns}")
        print(f"Normalized columns: {normalized_columns}")

        column_mapping = dict(
            zip(original_columns, normalized_columns)
        )

        expected_columns = {
            "ID",
            "Date",
            "Parameter/Paramètre",
            "Value/Valeur",
            "Symbol/Symbole",
        }

        if set(normalized_columns) != expected_columns:
            print("WARNING: unexpected column structure.")

        for row_number, row in enumerate(reader, start=2):
            row_count += 1

            if None in row:
                malformed_rows.append(row_number)
                continue

            normalized_row = {
                column_mapping[column]: value
                for column, value in row.items()
            }

            raw_values = list(row.values())

            if any(
                value != value.strip()
                for value in raw_values
                if value is not None
            ):
                whitespace_rows.append(row_number)

            station_value = normalized_row["ID"].strip()
            date_text = normalized_row["Date"].strip()
            parameter_value = normalized_row[
                "Parameter/Paramètre"
            ].strip()
            value_text = normalized_row["Value/Valeur"].strip()
            symbol_value = normalized_row["Symbol/Symbole"].strip()

            station_id_counts[station_value] += 1
            parameter_counts[parameter_value] += 1
            symbol_counts[symbol_value] += 1

            if station_value != station_id:
                unexpected_station_rows.append(
                    (row_number, station_value)
                )

            if parameter_value != EXPECTED_PARAMETER:
                unexpected_parameter_rows.append(
                    (row_number, parameter_value)
                )

            if symbol_value not in EXPECTED_SYMBOLS:
                unexpected_symbol_rows.append(
                    (row_number, symbol_value)
                )

            try:
                observation_date = date.fromisoformat(date_text)
            except ValueError:
                invalid_date_rows.append(
                    (row_number, date_text)
                )
            else:
                if not (
                    EXPECTED_START
                    <= observation_date
                    <= EXPECTED_END
                ):
                    invalid_date_rows.append(
                        (row_number, date_text)
                    )

            if not value_text:
                missing_value_rows.append(row_number)
                continue

            try:
                value = float(value_text)
            except ValueError:
                invalid_value_rows.append(
                    (row_number, value_text)
                )
                continue

            if not math.isfinite(value):
                invalid_value_rows.append(
                    (row_number, value_text)
                )
                continue

            if minimum_value is None or value < minimum_value:
                minimum_value = value

            if maximum_value is None or value > maximum_value:
                maximum_value = value

    print(f"\nRows: {row_count}")

    print("\nStation IDs:")
    for value, count in station_id_counts.items():
        print(f"  {value}: {count}")

    print("\nParameters:")
    for value, count in parameter_counts.items():
        print(f"  {value}: {count}")

    print("\nSymbols:")
    for value, count in symbol_counts.items():
        label = value if value else "(blank)"
        print(f"  {label}: {count}")

    print("\nCleaning-related checks:")
    print(f"  Missing water-level values: {len(missing_value_rows)}")
    print(f"  Invalid water-level values: {len(invalid_value_rows)}")
    print(f"  Invalid/out-of-range dates: {len(invalid_date_rows)}")
    print(f"  Unexpected station IDs: {len(unexpected_station_rows)}")
    print(f"  Unexpected parameters: {len(unexpected_parameter_rows)}")
    print(f"  Unexpected symbols: {len(unexpected_symbol_rows)}")
    print(f"  Rows with surrounding whitespace: {len(whitespace_rows)}")
    print(f"  Malformed CSV rows: {len(malformed_rows)}")

    print("\nWater-level range:")
    print(f"  Minimum: {minimum_value}")
    print(f"  Maximum: {maximum_value}")

    if missing_value_rows:
        print(
            "  Missing-value row examples: "
            f"{missing_value_rows[:10]}"
        )

    if invalid_value_rows:
        print(
            "  Invalid-value examples: "
            f"{invalid_value_rows[:10]}"
        )

    if invalid_date_rows:
        print(
            "  Invalid-date examples: "
            f"{invalid_date_rows[:10]}"
        )

    if unexpected_station_rows:
        print(
            "  Unexpected-station examples: "
            f"{unexpected_station_rows[:10]}"
        )

    if unexpected_parameter_rows:
        print(
            "  Unexpected-parameter examples: "
            f"{unexpected_parameter_rows[:10]}"
        )

    if unexpected_symbol_rows:
        print(
            "  Unexpected-symbol examples: "
            f"{unexpected_symbol_rows[:10]}"
        )

    if whitespace_rows:
        print(
            "  Whitespace-row examples: "
            f"{whitespace_rows[:10]}"
        )

    if malformed_rows:
        print(
            "  Malformed-row examples: "
            f"{malformed_rows[:10]}"
        )


def main() -> None:
    for station_id, path in FILES.items():
        inspect_file(station_id, path)


if __name__ == "__main__":
    main()