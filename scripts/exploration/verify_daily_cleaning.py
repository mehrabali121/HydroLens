import csv
from pathlib import Path


RAW_DAILY_DIR = Path("data/raw/daily")
PROCESSED_DAILY_DIR = Path("data/processed/daily")

STATIONS = [
    "01AF002",
    "01AK003",
    "01AO012",
    "01AP003",
]


def raw_path(station_id: str) -> Path:
    """Return the raw daily file for a station."""

    return (
        RAW_DAILY_DIR
        / station_id
        / f"wsc_{station_id}_daily_20110101_20241231.csv"
    )


def processed_path(station_id: str) -> Path:
    """Return the processed daily file for a station."""

    return (
        PROCESSED_DAILY_DIR
        / station_id
        / f"{station_id}_daily_20110101_20241231.csv"
    )


def read_raw_rows(
    path: Path,
) -> list[tuple[str, str, str, str, str]]:
    """Read raw observations into a comparable representation."""

    rows = []

    with path.open(
        "r",
        encoding="utf-8-sig",
        newline="",
    ) as file:
        reader = csv.DictReader(file)

        for row in reader:
            station_id = row[" ID"].strip()
            observation_date = row["Date"].strip()
            parameter = row["Parameter/Paramètre"].strip()
            water_level = row["Value/Valeur"].strip()
            quality_symbol = row["Symbol/Symbole"].strip()

            rows.append(
                (
                    station_id,
                    observation_date,
                    parameter,
                    water_level,
                    quality_symbol,
                )
            )

    return rows


def read_processed_rows(
    path: Path,
) -> list[tuple[str, str, str, str, str]]:
    """Read processed observations into the same representation."""

    rows = []

    with path.open(
        "r",
        encoding="utf-8",
        newline="",
    ) as file:
        reader = csv.DictReader(file)

        for row in reader:
            rows.append(
                (
                    row["station_id"],
                    row["date"],
                    row["parameter"],
                    row["water_level_m"],
                    row["quality_symbol"],
                )
            )

    return rows


def verify_station(station_id: str) -> None:
    """Compare raw and processed observations for one station."""

    raw = read_raw_rows(raw_path(station_id))
    processed = read_processed_rows(
        processed_path(station_id)
    )

    if len(raw) != len(processed):
        raise ValueError(
            f"{station_id}: row count changed "
            f"from {len(raw)} to {len(processed)}."
        )

    differences = []

    for row_number, (raw_row, processed_row) in enumerate(
        zip(raw, processed),
        start=2,
    ):
        (
            raw_station,
            raw_date,
            raw_parameter,
            raw_value,
            raw_symbol,
        ) = raw_row

        (
            processed_station,
            processed_date,
            processed_parameter,
            processed_value,
            processed_symbol,
        ) = processed_row

        if (
            raw_station != processed_station
            or raw_date != processed_date
            or raw_parameter != processed_parameter
            or raw_value != processed_value
            or raw_symbol != processed_symbol
        ):
            differences.append(
                (
                    row_number,
                    raw_row,
                    processed_row,
                )
            )

            if len(differences) >= 5:
                break

    processed_keys = [
        (
            station,
            observation_date,
        )
        for station, observation_date, _, _, _ in processed
    ]

    duplicate_keys = {
        key
        for key in processed_keys
        if processed_keys.count(key) > 1
    }

    print(f"\nStation: {station_id}")
    print(f"Raw rows: {len(raw)}")
    print(f"Processed rows: {len(processed)}")
    print(f"Changed rows: {len(differences)}")
    print(f"Duplicate station/date keys: {len(duplicate_keys)}")

    if differences:
        print("\nFirst differences:")

        for row_number, raw_row, processed_row in differences:
            print(f"  Row {row_number}")
            print(f"    Raw:       {raw_row}")
            print(f"    Processed: {processed_row}")

        raise ValueError(
            f"{station_id}: processed data does not "
            "match raw observations."
        )

    if duplicate_keys:
        print("\nDuplicate keys:")

        for key in sorted(duplicate_keys):
            print(f"  {key}")

        raise ValueError(
            f"{station_id}: processed data contains "
            "duplicate station/date keys."
        )

    print("Result: PASS")


def main() -> None:
    """Verify all processed daily station files."""

    for station_id in STATIONS:
        verify_station(station_id)

    print("\nAll daily cleaning checks passed.")


if __name__ == "__main__":
    main()