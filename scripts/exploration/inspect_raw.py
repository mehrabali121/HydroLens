import csv
from collections import Counter
from datetime import datetime, date, timedelta
from pathlib import Path


RAW_DIR = Path("data/raw")


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


def read_csv(file_path: Path) -> tuple[list[str], list[dict[str, str]]]:
    with file_path.open(
        "r",
        encoding="utf-8-sig",
        newline="",
    ) as file:
        reader = csv.DictReader(file)
        rows = list(reader)

        if reader.fieldnames is None:
            raise ValueError(f"No header found in {file_path}")

        return reader.fieldnames, rows


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
        print(
            "Columns with surrounding whitespace: "
            f"{whitespace_columns}"
        )

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

    for number, (schema, files) in enumerate(
        schemas.items(),
        start=1,
    ):
        print(f"\nSchema {number}:")
        print(f"Columns: {list(schema)}")

        print("Files:")
        for file_name in files:
            print(f"  - {file_name}")


def inspect_row_structure(file_path: Path) -> None:
    print("=" * 70)
    print(f"ROW STRUCTURE VALIDATION: {file_path.name}")

    try:
        raw_text = file_path.read_text(
            encoding="utf-8-sig"
        )
    except UnicodeDecodeError:
        print(
            "Unable to inspect rows because "
            "UTF-8 decoding failed."
        )
        return

    lines = raw_text.splitlines()

    if not lines:
        print("Empty file: FAIL")
        return

    header = lines[0].split(",")
    expected_column_count = len(header)

    malformed_rows = 0
    empty_rows = 0

    for line_number, line in enumerate(
        lines[1:],
        start=2,
    ):
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

    print(
        f"Expected fields per row: "
        f"{expected_column_count}"
    )
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
        print(
            f"Missing expected columns: "
            f"{sorted(missing_columns)}"
        )
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


def inspect_station_and_parameter(file_path: Path) -> None:
    columns, rows = read_csv(file_path)

    print("=" * 70)
    print(
        f"STATION/PARAMETER VALIDATION: "
        f"{file_path.name}"
    )

    if not rows:
        print("No rows to inspect.")
        return

    station_column = " ID"
    parameter_column = "Parameter/Paramètre"

    if station_column not in columns:
        print("Missing station ID column")
        return

    if parameter_column not in columns:
        print("Missing parameter column")
        return

    station_ids = Counter(
        row[station_column]
        for row in rows
    )

    parameters = Counter(
        row[parameter_column]
        for row in rows
    )

    print("Station IDs:")

    for station_id, count in station_ids.items():
        print(
            f"  {station_id!r}: {count}"
        )

    print("Parameters:")

    for parameter, count in parameters.items():
        print(
            f"  {parameter!r}: {count}"
        )


def inspect_expected_station(file_path: Path) -> None:
    columns, rows = read_csv(file_path)

    if not rows or " ID" not in columns:
        return

    station_ids = {
        row[" ID"]
        for row in rows
    }

    expected_station = None

    for station_name, station_id in EXPECTED_STATIONS.items():
        if station_name in file_path.name.lower():
            expected_station = station_id
            break

    print("=" * 70)
    print(
        f"EXPECTED STATION CHECK: "
        f"{file_path.name}"
    )

    if expected_station is None:
        print(
            "No expected station mapping "
            "found for this filename."
        )
        return

    print(f"Expected station: {expected_station}")
    print(
        f"Station IDs found: "
        f"{sorted(station_ids)}"
    )

    if station_ids == {expected_station}:
        print("Result: PASS")
    else:
        print("Result: FAIL")


def inspect_expected_parameter(file_path: Path) -> None:
    columns, rows = read_csv(file_path)

    if not rows or "Parameter/Paramètre" not in columns:
        return

    parameters = {
        row["Parameter/Paramètre"]
        for row in rows
    }

    if "unit" in file_path.name.lower():
        expected_parameter = EXPECTED_UNIT_PARAMETER
    else:
        expected_parameter = EXPECTED_DAILY_PARAMETER

    print("=" * 70)
    print(
        f"EXPECTED PARAMETER CHECK: "
        f"{file_path.name}"
    )

    print(
        f"Expected parameter: "
        f"{expected_parameter}"
    )

    print(
        f"Parameters found: "
        f"{sorted(parameters)}"
    )

    if parameters == {expected_parameter}:
        print("Result: PASS")
    else:
        print("Result: FAIL")


def inspect_values_and_quality(file_path: Path) -> None:
    columns, rows = read_csv(file_path)

    if not rows:
        return

    print("=" * 70)
    print(
        f"VALUE/QUALITY INSPECTION: "
        f"{file_path.name}"
    )

    numeric_values = []
    blank_values = 0
    invalid_values = 0

    parameter_counts: Counter[str] = Counter()
    symbol_counts: Counter[str] = Counter()

    approval_counts: Counter[str] = Counter()
    grade_counts: Counter[str] = Counter()
    qualifier_counts: Counter[str] = Counter()
    qualifiers_counts: Counter[str] = Counter()

    for row in rows:
        raw_value = row["Value/Valeur"].strip()

        if not raw_value:
            blank_values += 1
        else:
            try:
                numeric_values.append(
                    float(raw_value)
                )
            except ValueError:
                invalid_values += 1

        parameter_counts[
            row["Parameter/Paramètre"]
        ] += 1

        if "Symbol/Symbole" in row:
            symbol_counts[
                row["Symbol/Symbole"].strip()
            ] += 1

        if "Approval/Approbation" in row:
            approval_counts[
                row["Approval/Approbation"].strip()
            ] += 1

        if "Grade/Classification" in row:
            grade_counts[
                row["Grade/Classification"].strip()
            ] += 1

        if "Qualifier/Qualificatif" in row:
            qualifier_counts[
                row["Qualifier/Qualificatif"].strip()
            ] += 1

        if "Qualifiers/Qualificatifs" in row:
            qualifiers_counts[
                row["Qualifiers/Qualificatifs"].strip()
            ] += 1

    print(f"Rows: {len(rows)}")
    print(f"Numeric values: {len(numeric_values)}")
    print(f"Blank values: {blank_values}")
    print(f"Invalid numeric values: {invalid_values}")

    if numeric_values:
        print(
            f"Minimum value: "
            f"{min(numeric_values)}"
        )
        print(
            f"Maximum value: "
            f"{max(numeric_values)}"
        )

    print(
        f"Parameter values: "
        f"{dict(parameter_counts)}"
    )

    if symbol_counts:
        print(
            f"Symbol values: "
            f"{dict(symbol_counts)}"
        )

    if approval_counts:
        print(
            f"Approval values: "
            f"{dict(approval_counts)}"
        )

    if grade_counts:
        print(
            f"Grade values: "
            f"{dict(grade_counts)}"
        )

    if qualifier_counts:
        print(
            f"Qualifier values: "
            f"{dict(qualifier_counts)}"
        )

    if qualifiers_counts:
        print(
            f"Qualifiers values: "
            f"{dict(qualifiers_counts)}"
        )


def parse_daily_date(value: str) -> date:
    return datetime.strptime(
        value,
        "%Y-%m-%d",
    ).date()


def parse_unit_timestamp(value: str) -> datetime:
    return datetime.fromisoformat(
        value.replace("Z", "+00:00")
    )


def inspect_daily_dates(file_path: Path) -> None:
    columns, rows = read_csv(file_path)

    if "Date" not in columns or not rows:
        return

    dates = [
        parse_daily_date(row["Date"])
        for row in rows
    ]

    duplicate_count = sum(
        count - 1
        for count in Counter(dates).values()
        if count > 1
    )

    backward_count = sum(
        current < previous
        for previous, current in zip(
            dates,
            dates[1:],
        )
    )

    first_date = min(dates)
    last_date = max(dates)

    expected_dates = (
        last_date - first_date
    ).days + 1

    observed_dates = set(dates)

    missing_dates = [
        first_date + timedelta(days=offset)
        for offset in range(expected_dates)
        if first_date + timedelta(days=offset)
        not in observed_dates
    ]

    print("=" * 70)
    print(
        f"DAILY DATE/COVERAGE VALIDATION: "
        f"{file_path.name}"
    )

    print(f"Rows: {len(dates)}")
    print(f"First date: {first_date}")
    print(f"Last date: {last_date}")
    print(
        f"Calendar days in span: "
        f"{expected_dates}"
    )
    print(
        f"Missing calendar dates: "
        f"{len(missing_dates)}"
    )
    print(
        f"Duplicate dates: "
        f"{duplicate_count}"
    )
    print(
        f"Backward date transitions: "
        f"{backward_count}"
    )

    if missing_dates:
        print("Missing dates:")

        for missing_date in missing_dates:
            print(f"  {missing_date}")

    if (
        len(missing_dates) == 0
        and duplicate_count == 0
        and backward_count == 0
    ):
        print("Result: PASS")
    else:
        print("Result: REVIEW")


def inspect_unit_timestamps(file_path: Path) -> None:
    columns, rows = read_csv(file_path)

    if "Date" not in columns or not rows:
        return

    timestamps = [
        parse_unit_timestamp(row["Date"])
        for row in rows
    ]

    intervals = [
        (
            previous,
            current,
            int(
                (
                    current - previous
                ).total_seconds()
            ),
        )
        for previous, current in zip(
            timestamps,
            timestamps[1:],
        )
    ]

    interval_seconds = [
        seconds
        for _, _, seconds in intervals
    ]

    interval_counts = Counter(
        interval_seconds
    )

    duplicate_count = sum(
        count - 1
        for count in Counter(
            timestamps
        ).values()
        if count > 1
    )

    backward_count = sum(
        current < previous
        for previous, current in zip(
            timestamps,
            timestamps[1:],
        )
    )

    timezone_aware_count = sum(
        timestamp.tzinfo is not None
        and timestamp.utcoffset() is not None
        for timestamp in timestamps
    )

    unusual_intervals = [
        (
            previous,
            current,
            seconds,
        )
        for previous, current, seconds in intervals
        if seconds != 300
    ]

    largest_gap = (
        max(interval_seconds)
        if interval_seconds
        else None
    )

    largest_gap_details = None

    if interval_seconds:
        largest_gap_details = max(
            intervals,
            key=lambda item: item[2],
        )

    print("=" * 70)
    print(
        f"UNIT TIMESTAMP/COVERAGE VALIDATION: "
        f"{file_path.name}"
    )

    print(f"Observations: {len(timestamps)}")
    print(
        f"First timestamp: "
        f"{timestamps[0]}"
    )
    print(
        f"Last timestamp: "
        f"{timestamps[-1]}"
    )

    print(
        f"Timezone-aware timestamps: "
        f"{timezone_aware_count}/"
        f"{len(timestamps)}"
    )

    print(
        f"Backward timestamp transitions: "
        f"{backward_count}"
    )

    print(
        f"Duplicate timestamps: "
        f"{duplicate_count}"
    )

    if interval_seconds:
        print(
            f"Minimum interval: "
            f"{min(interval_seconds)} seconds"
        )

        print(
            f"Maximum interval: "
            f"{max(interval_seconds)} seconds"
        )

        print(
            f"Most common interval: "
            f"{interval_counts.most_common(1)[0][0]} "
            f"seconds"
        )

        print(
            f"Non-5-minute intervals: "
            f"{len(unusual_intervals)}"
        )

        print(
            f"Largest gap: "
            f"{largest_gap} seconds"
        )

        if largest_gap_details:
            previous, current, seconds = (
                largest_gap_details
            )

            print(
                f"Largest gap details: "
                f"{previous} -> {current} "
                f"({seconds} seconds)"
            )

    if (
        backward_count == 0
        and duplicate_count == 0
        and timezone_aware_count == len(timestamps)
    ):
        print("Timestamp ordering/timezone result: PASS")
    else:
        print(
            "Timestamp ordering/timezone result: "
            "REVIEW"
        )


def inspect_file(file_path: Path) -> None:
    inspect_csv(file_path)
    inspect_encoding_and_headers(file_path)
    inspect_row_structure(file_path)
    inspect_required_fields(file_path)
    inspect_station_and_parameter(file_path)
    inspect_expected_station(file_path)
    inspect_expected_parameter(file_path)
    inspect_values_and_quality(file_path)

    if "unit" in file_path.name.lower():
        inspect_unit_timestamps(file_path)
    else:
        inspect_daily_dates(file_path)


def main() -> None:
    csv_files = sorted(
        RAW_DIR.glob("*.csv")
    )

    print(
        f"Found {len(csv_files)} CSV files."
    )

    if not csv_files:
        print(
            "No CSV files found in "
            f"{RAW_DIR}"
        )
        return

    for file_path in csv_files:
        inspect_file(file_path)

    compare_schemas(csv_files)


if __name__ == "__main__":
    main()