import csv
from collections import Counter
from datetime import datetime
from pathlib import Path


RAW_DIR = Path("data/raw")


def read_csv(file_path: Path) -> tuple[list[str], list[dict[str, str]]]:
    with file_path.open("r", encoding="utf-8-sig", newline="") as file:
        reader = csv.DictReader(file)
        rows = list(reader)

        if reader.fieldnames is None:
            raise ValueError(f"No header found in {file_path}")

        return reader.fieldnames, rows


def inspect_csv(file_path: Path) -> None:
    print("=" * 70)
    print(f"FILE: {file_path.name}")

    columns, rows = read_csv(file_path)

    print(f"Columns: {columns}")
    print(f"Rows: {len(rows)}")

    whitespace_columns = [
        column for column in columns
        if column != column.strip()
    ]

    if whitespace_columns:
        print(f"Columns with surrounding whitespace: {whitespace_columns}")

    if rows:
        print(f"First row: {rows[0]}")
        print(f"Last row:  {rows[-1]}")


def compare_schemas(csv_files: list[Path]) -> None:
    print("=" * 70)
    print("SCHEMA COMPARISON")

    schemas: dict[tuple[str, ...], list[str]] = {}

    for file_path in csv_files:
        columns, _ = read_csv(file_path)
        schema = tuple(columns)

        schemas.setdefault(schema, []).append(file_path.name)

    print(f"Unique schemas found: {len(schemas)}")

    for number, (schema, files) in enumerate(schemas.items(), start=1):
        print(f"\nSchema {number}:")
        print(f"Columns: {list(schema)}")

        print("Files:")
        for file_name in files:
            print(f"  - {file_name}")


def inspect_unit_timestamps(file_path: Path) -> None:
    columns, rows = read_csv(file_path)

    if "Date" not in columns:
        return

    if not rows:
        return

    timestamps = [
        datetime.fromisoformat(row["Date"].replace("Z", "+00:00"))
        for row in rows
    ]

    intervals = [
        (previous, current, int((current - previous).total_seconds()))
        for previous, current in zip(timestamps, timestamps[1:])
    ]

    interval_seconds = [interval for _, _, interval in intervals]

    interval_counts = Counter(interval_seconds)

    duplicate_count = sum(
        count - 1
        for count in Counter(timestamps).values()
        if count > 1
    )

    unusual_intervals = [
        (previous, current, seconds)
        for previous, current, seconds in intervals
        if seconds != 300
    ]

    print("=" * 70)
    print(f"TIMESTAMP ANALYSIS: {file_path.name}")
    print(f"First timestamp: {timestamps[0]}")
    print(f"Last timestamp:  {timestamps[-1]}")
    print(f"Observations: {len(timestamps)}")

    if interval_seconds:
        print(f"Minimum interval: {min(interval_seconds)} seconds")
        print(f"Maximum interval: {max(interval_seconds)} seconds")
        print(
            f"Most common interval: "
            f"{interval_counts.most_common(1)[0][0]} seconds"
        )

    print(f"Duplicate timestamps: {duplicate_count}")
    print(f"Non-5-minute intervals: {len(unusual_intervals)}")

    if unusual_intervals:
        print("Unusual intervals:")

        for previous, current, seconds in unusual_intervals:
            print(
                f"  {previous} -> {current}: "
                f"{seconds} seconds"
            )


def inspect_timestamp_order(file_path: Path) -> None:
    columns, rows = read_csv(file_path)

    if "Date" not in columns or not rows:
        return

    timestamps = [
        datetime.fromisoformat(row["Date"].replace("Z", "+00:00"))
        for row in rows
    ]

    backward_count = sum(
        current < previous
        for previous, current in zip(timestamps, timestamps[1:])
    )

    duplicate_count = sum(
        count - 1
        for count in Counter(timestamps).values()
        if count > 1
    )

    timezone_aware_count = sum(
        timestamp.tzinfo is not None
        and timestamp.utcoffset() is not None
        for timestamp in timestamps
    )

    print("=" * 70)
    print(f"TIMESTAMP VALIDATION: {file_path.name}")
    print(f"Rows checked: {len(timestamps)}")
    print(f"Backward timestamp transitions: {backward_count}")
    print(f"Duplicate timestamps: {duplicate_count}")
    print(
        f"Timezone-aware timestamps: "
        f"{timezone_aware_count}/{len(timestamps)}"
    )


def inspect_daily_date_order(file_path: Path) -> None:
    columns, rows = read_csv(file_path)

    if "Date" not in columns or not rows:
        return

    dates = [
    datetime.strptime(row["Date"], "%Y-%m-%d").date()
    for row in rows
    ]

    backward_count = sum(
        current < previous
        for previous, current in zip(dates, dates[1:])
    )

    duplicate_count = sum(
        count - 1
        for count in Counter(dates).values()
        if count > 1
    )

    print("=" * 70)
    print(f"DAILY DATE VALIDATION: {file_path.name}")
    print(f"Rows checked: {len(dates)}")
    print(f"Backward date transitions: {backward_count}")
    print(f"Duplicate dates: {duplicate_count}")
    print(f"First date: {dates[0]}")
    print(f"Last date: {dates[-1]}")


def inspect_values_and_quality(file_path: Path) -> None:
    columns, rows = read_csv(file_path)

    if not rows:
        return

    value_column = "Value/Valeur"

    if value_column not in columns:
        return

    values = []
    blank_values = 0
    invalid_values = []

    for row_number, row in enumerate(rows, start=2):
        raw_value = row[value_column].strip()

        if not raw_value:
            blank_values += 1
            continue

        try:
            values.append(float(raw_value))
        except ValueError:
            invalid_values.append((row_number, raw_value))

    print("=" * 70)
    print(f"VALUE AND QUALITY INSPECTION: {file_path.name}")
    print(f"Rows checked: {len(rows)}")
    print(f"Numeric values: {len(values)}")
    print(f"Blank values: {blank_values}")
    print(f"Invalid numeric values: {len(invalid_values)}")

    if values:
        print(f"Minimum value: {min(values)}")
        print(f"Maximum value: {max(values)}")

    if invalid_values:
        print("Invalid values:")

        for row_number, raw_value in invalid_values[:10]:
            print(
                f"  Row {row_number}: {raw_value!r}"
            )

    for column in [
        "Parameter/Paramètre",
        "Symbol/Symbole",
        "Approval/Approbation",
        "Grade/Classification",
        "Qualifier/Qualificatif",
        "Qualifiers/Qualificatifs",
    ]:
        if column in columns:
            counts = Counter(
                row[column].strip()
                for row in rows
            )

            print(f"{column}:")

            for value, count in counts.items():
                print(f"  {value!r}: {count}")


def inspect_station_and_parameter(file_path: Path) -> None:
    columns, rows = read_csv(file_path)

    if not rows:
        return

    station_column = " ID"
    parameter_column = "Parameter/Paramètre"

    if station_column not in columns:
        print("=" * 70)
        print(f"STATION/PARAMETER VALIDATION: {file_path.name}")
        print("Missing station ID column")
        return

    if parameter_column not in columns:
        print("=" * 70)
        print(f"STATION/PARAMETER VALIDATION: {file_path.name}")
        print("Missing parameter column")
        return

    station_ids = Counter(row[station_column] for row in rows)
    parameters = Counter(row[parameter_column] for row in rows)

    print("=" * 70)
    print(f"STATION/PARAMETER VALIDATION: {file_path.name}")

    print("Station IDs:")
    for station_id, count in station_ids.items():
        print(f"  {station_id!r}: {count}")

    print("Parameters:")
    for parameter, count in parameters.items():
        print(f"  {parameter!r}: {count}")


EXPECTED_STATIONS = {
    "grand_falls": "01AF002",
    "fredericton": "01AK003",
    "gagetown": "01AO012",
    "oak_point": "01AP003",
}

EXPECTED_DAILY_PARAMETER = "water level/niveau"
EXPECTED_UNIT_PARAMETER = "46"

EXPECTED_DAILY_COLUMNS = {
    " ID",
    "Date",
    "Parameter/Paramètre",
    "Value/Valeur",
    "Symbol/Symbole",
}

EXPECTED_UNIT_COLUMNS = {
    " ID",
    "Date",
    "Parameter/Paramètre",
    "Value/Valeur",
    "Qualifier/Qualificatif",
    "Symbol/Symbole",
    "Approval/Approbation",
    "Grade/Classification",
    "Qualifiers/Qualificatifs",
}

REQUIRED_VALUE_COLUMNS = {
    " ID",
    "Date",
    "Parameter/Paramètre",
    "Value/Valeur",
}

def inspect_expected_station(file_path: Path) -> None:
    columns, rows = read_csv(file_path)

    if not rows or " ID" not in columns:
        return

    station_ids = set(row[" ID"] for row in rows)

    expected_station = None

    for station_name, station_id in EXPECTED_STATIONS.items():
        if station_name in file_path.name.lower():
            expected_station = station_id
            break

    print("=" * 70)
    print(f"EXPECTED STATION CHECK: {file_path.name}")

    if expected_station is None:
        print("No expected station mapping found for this filename.")
        return

    print(f"Expected station: {expected_station}")
    print(f"Station IDs found: {sorted(station_ids)}")

    if station_ids == {expected_station}:
        print("Result: PASS")
    else:
        print("Result: FAIL")

def inspect_expected_parameter(file_path: Path) -> None:
    columns, rows = read_csv(file_path)

    if not rows or "Parameter/Paramètre" not in columns:
        return

    parameters = set(row["Parameter/Paramètre"] for row in rows)

    if "unit" in file_path.name.lower():
        expected_parameter = EXPECTED_UNIT_PARAMETER
    else:
        expected_parameter = EXPECTED_DAILY_PARAMETER

    print("=" * 70)
    print(f"EXPECTED PARAMETER CHECK: {file_path.name}")

    print(f"Expected parameter: {expected_parameter}")
    print(f"Parameters found: {sorted(parameters)}")

    if parameters == {expected_parameter}:
        print("Result: PASS")
    else:
        print("Result: FAIL")

def inspect_encoding_and_headers(file_path: Path) -> None:
    print("=" * 70)
    print(f"ENCODING/HEADER VALIDATION: {file_path.name}")

    try:
        raw_bytes = file_path.read_bytes()
        raw_bytes.decode("utf-8-sig")
    except UnicodeDecodeError as error:
        print(f"UTF-8 decoding: FAIL ({error})")
        return

    print("UTF-8 decoding: PASS")

    columns, _ = read_csv(file_path)

    if not columns:
        print("Header: FAIL (empty header)")
        return

    if any(not column.strip() for column in columns):
        print("Header: FAIL (blank column name)")
        return

    print(f"Header: PASS ({len(columns)} columns)")
    print(f"Columns: {columns}")

def inspect_row_structure(file_path: Path) -> None:
    print("=" * 70)
    print(f"ROW STRUCTURE VALIDATION: {file_path.name}")

    try:
        raw_text = file_path.read_text(encoding="utf-8-sig")
    except UnicodeDecodeError:
        print("Unable to inspect rows because UTF-8 decoding failed.")
        return

    lines = raw_text.splitlines()

    if not lines:
        print("Empty file: FAIL")
        return

    header = lines[0].split(",")

    expected_column_count = len(header)

    malformed_rows = 0
    empty_rows = 0

    for line_number, line in enumerate(lines[1:], start=2):
        if not line.strip():
            empty_rows += 1
            continue

        fields = line.split(",")

        if len(fields) != expected_column_count:
            malformed_rows += 1
            print(
                f"Malformed row at line {line_number}: "
                f"expected {expected_column_count} fields, "
                f"found {len(fields)}"
            )

    print(f"Expected fields per row: {expected_column_count}")
    print(f"Malformed rows: {malformed_rows}")
    print(f"Empty rows: {empty_rows}")

    if malformed_rows == 0 and empty_rows == 0:
        print("Result: PASS")
    else:
        print("Result: REVIEW")

def inspect_required_fields(file_path: Path) -> None:
    columns, rows = read_csv(file_path)

    print("=" * 70)
    print(f"REQUIRED FIELD VALIDATION: {file_path.name}")

    if "unit" in file_path.name.lower():
        expected_columns = EXPECTED_UNIT_COLUMNS
    else:
        expected_columns = EXPECTED_DAILY_COLUMNS

    missing_columns = expected_columns - set(columns)

    if missing_columns:
        print(f"Missing expected columns: {sorted(missing_columns)}")
        print("Result: FAIL")
        return

    print("Expected columns: PASS")

    empty_fields: Counter[str] = Counter()

    for row in rows:
        for column in REQUIRED_VALUE_COLUMNS:
            if not row[column].strip():
                empty_fields[column] += 1

    if empty_fields:
        print("Empty required fields:")
        for column, count in empty_fields.items():
            print(f"  {column!r}: {count}")

        print("Result: FAIL")
    else:
        print("Empty required fields: 0")
        print("Result: PASS")


def main() -> None:
    csv_files = sorted(RAW_DIR.glob("*.csv"))

    print(f"Found {len(csv_files)} CSV files.")

    for file_path in csv_files:
        inspect_csv(file_path)

    compare_schemas(csv_files)

    unit_files = [
        file_path
        for file_path in csv_files
        if "unit" in file_path.name.lower()
    ]

    for file_path in unit_files:
        inspect_unit_timestamps(file_path)
        inspect_timestamp_order(file_path)
       
    daily_files = [
        file_path
        for file_path in csv_files
        if "unit" not in file_path.name.lower()
    ]

    for file_path in daily_files:
        inspect_daily_date_order(file_path)

    for file_path in csv_files:
        inspect_values_and_quality(file_path)
        inspect_station_and_parameter(file_path)
        inspect_expected_station(file_path)
        inspect_expected_parameter(file_path)
        inspect_encoding_and_headers(file_path)
        inspect_row_structure(file_path)
        inspect_required_fields(file_path)

if __name__ == "__main__":
    main()