from argparse import ArgumentParser, ArgumentTypeError
from datetime import date
from pathlib import Path
from urllib.parse import urlencode
from urllib.request import urlopen


BASE_URL = "https://wateroffice.ec.gc.ca/services/daily_data/csv/inline"
RAW_DAILY_DIR = Path("data/raw/daily")


def parse_date(value: str) -> date:
    """Convert YYYY-MM-DD text into a date."""
    try:
        return date.fromisoformat(value)
    except ValueError as error:
        raise ArgumentTypeError(
            f"invalid date '{value}'; use YYYY-MM-DD"
        ) from error


def parse_station_id(value: str) -> str:
    """Validate the basic format of a WSC station ID."""
    station_id = value.strip().upper()

    if len(station_id) != 7 or not station_id.isalnum():
        raise ArgumentTypeError(
            "station ID must be a 7-character alphanumeric WSC ID"
        )

    return station_id


def download_daily_water_level(
    station_id: str,
    start_date: str,
    end_date: str,
    output_file: Path,
) -> int:
    """Download daily water-level data for one WSC station."""

    params = [
        ("stations[]", station_id),
        ("parameters[]", "level"),
        ("start_date", start_date),
        ("end_date", end_date),
    ]

    url = f"{BASE_URL}?{urlencode(params)}"

    output_file.parent.mkdir(parents=True, exist_ok=True)

    with urlopen(url, timeout=30) as response:
        data = response.read()

    if not data:
        raise ValueError("WSC returned an empty response.")

    output_file.write_bytes(data)

    return len(data)


def build_output_path(
    station_id: str,
    start_date: str,
    end_date: str,
) -> Path:
    """Create the raw output path for one station."""

    start_text = start_date.replace("-", "")
    end_text = end_date.replace("-", "")

    return (
        RAW_DAILY_DIR
        / station_id
        / f"wsc_{station_id}_daily_{start_text}_{end_text}.csv"
    )


def parse_arguments() -> tuple[str, str, str]:
    """Read and validate command-line arguments."""

    parser = ArgumentParser(
        description="Download WSC daily water-level data."
    )

    parser.add_argument(
        "--station",
        required=True,
        type=parse_station_id,
        help="WSC station ID, for example 01AF002.",
    )

    parser.add_argument(
        "--start",
        required=True,
        type=parse_date,
        help="Start date in YYYY-MM-DD format.",
    )

    parser.add_argument(
        "--end",
        required=True,
        type=parse_date,
        help="End date in YYYY-MM-DD format.",
    )

    args = parser.parse_args()

    if args.end < args.start:
        parser.error("--end must be on or after --start.")

    return (
        args.station,
        args.start.isoformat(),
        args.end.isoformat(),
    )


def main() -> None:
    station_id, start_date, end_date = parse_arguments()

    output_file = build_output_path(
        station_id,
        start_date,
        end_date,
    )

    byte_count = download_daily_water_level(
        station_id=station_id,
        start_date=start_date,
        end_date=end_date,
        output_file=output_file,
    )

    print(f"Station: {station_id}")
    print(f"Date range: {start_date} to {end_date}")
    print(f"Downloaded: {byte_count} bytes")
    print(f"Saved to: {output_file}")


if __name__ == "__main__":
    main()