import csv
from datetime import date
from pathlib import Path


RAW_DAILY_DIR = Path("data/raw/daily")
PROCESSED_DAILY_DIR = Path("data/processed/daily")

EXPECTED_START = date(2011, 1, 1)
EXPECTED_END = date(2024, 12, 31)

EXPECTED_PARAMETER = "water level/niveau"
EXPECTED_SYMBOLS = {"", "A", "E"}

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


OUTPUT_COLUMNS = [
    "station_id",
    "date",
    "parameter",
    "water_level_m",
    "quality_symbol",
]


def build_output_path(station_id: str) -> Path:
    """Build the processed output path for one station."""

    return (
        PROCESSED_DAILY_DIR
        / station_id
        / f"{station_id}_daily_20110101_20241231.csv"
    )


def normalize_headers(
    fieldnames: list[str] | None,
) -> dict[str, str]:
    """Normalize source header names without modifying the raw file."""

    if fieldnames is None:
        raise ValueError("CSV file has no header row.")

    normalized_columns = [
        column.strip()
        for column in fieldnames
    ]

    column_mapping = dict(
        zip(fieldnames, normalized_columns)
    )

    expected_columns = {
        "ID",
        "Date",
        "Parameter/Paramètre",
        "Value/Valeur",
        "Symbol/Symbole",
    }

    if set(normalized_columns) != expected_columns:
        raise ValueError(
            "Unexpected WSC CSV columns: "
            f"{normalized_columns}"
        )

    return column_mapping


def clean_station(
    station_id: str,
    input_path: Path,
    output_path: Path,
) -> dict[str, int]:
    """Clean one raw WSC daily file."""

    output_path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    rows_processed = 0
    rows_written = 0

    with input_path.open(
        "r",
        encoding="utf-8-sig",
        newline="",
    ) as input_file, output_path.open(
        "w",
        encoding="utf-8",
        newline="",
    ) as output_file:

        reader = csv.DictReader(input_file)

        column_mapping = normalize_headers(
            reader.fieldnames
        )

        writer = csv.DictWriter(
            output_file,
            fieldnames=OUTPUT_COLUMNS,
        )

        writer.writeheader()

        for row_number, row in enumerate(
            reader,
            start=2,
        ):
            rows_processed += 1

            if None in row:
                raise ValueError(
                    f"{input_path}: malformed CSV row "
                    f"at line {row_number}."
                )

            normalized_row = {
                column_mapping[column]: value
                for column, value in row.items()
            }

            source_station_id = normalized_row["ID"].strip()
            date_text = normalized_row["Date"].strip()
            parameter = normalized_row[
                "Parameter/Paramètre"
            ].strip()
            value_text = normalized_row[
                "Value/Valeur"
            ].strip()
            quality_symbol = normalized_row[
                "Symbol/Symbole"
            ].strip()

            if source_station_id != station_id:
                raise ValueError(
                    f"{input_path}: unexpected station ID "
                    f"'{source_station_id}' at line "
                    f"{row_number}."
                )

            if parameter != EXPECTED_PARAMETER:
                raise ValueError(
                    f"{input_path}: unexpected parameter "
                    f"'{parameter}' at line {row_number}."
                )

            if quality_symbol not in EXPECTED_SYMBOLS:
                raise ValueError(
                    f"{input_path}: unexpected quality symbol "
                    f"'{quality_symbol}' at line {row_number}."
                )

            try:
                observation_date = date.fromisoformat(
                    date_text
                )
            except ValueError as error:
                raise ValueError(
                    f"{input_path}: invalid date "
                    f"'{date_text}' at line {row_number}."
                ) from error

            if not (
                EXPECTED_START
                <= observation_date
                <= EXPECTED_END
            ):
                raise ValueError(
                    f"{input_path}: date '{date_text}' "
                    f"is outside the expected range at "
                    f"line {row_number}."
                )

            if not value_text:
                raise ValueError(
                    f"{input_path}: missing water level "
                    f"at line {row_number}."
                )

            try:
                water_level = float(value_text)
            except ValueError as error:
                raise ValueError(
                    f"{input_path}: invalid water level "
                    f"'{value_text}' at line {row_number}."
                ) from error

            writer.writerow(
                {
                    "station_id": source_station_id,
                    "date": observation_date.isoformat(),
                    "parameter": parameter,
                    "water_level_m": f"{water_level:.3f}",
                    "quality_symbol": quality_symbol,
                }
            )

            rows_written += 1

    return {
        "rows_processed": rows_processed,
        "rows_written": rows_written,
    }


def main() -> None:
    """Clean all configured WSC daily files."""

    total_processed = 0
    total_written = 0

    for station_id, input_path in FILES.items():
        output_path = build_output_path(station_id)

        summary = clean_station(
            station_id=station_id,
            input_path=input_path,
            output_path=output_path,
        )

        total_processed += summary["rows_processed"]
        total_written += summary["rows_written"]

        print(f"\nStation: {station_id}")
        print(f"Input: {input_path}")
        print(f"Output: {output_path}")
        print(
            f"Rows processed: "
            f"{summary['rows_processed']}"
        )
        print(
            f"Rows written: "
            f"{summary['rows_written']}"
        )

    print("\nCleaning complete.")
    print(f"Total rows processed: {total_processed}")
    print(f"Total rows written: {total_written}")


if __name__ == "__main__":
    main()