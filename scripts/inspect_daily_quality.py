import csv
from collections import Counter
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


def inspect_station(station_id: str, path: Path) -> None:
    """Count daily WSC symbols for one station."""

    symbols = Counter()
    total_rows = 0

    with path.open("r", encoding="utf-8-sig", newline="") as file:
        reader = csv.DictReader(file)

        for row in reader:
            total_rows += 1

            symbol = row["Symbol/Symbole"].strip()

            if not symbol:
                symbol = "(blank)"

            symbols[symbol] += 1

    print(f"\nStation: {station_id}")
    print(f"Total rows: {total_rows}")
    print("Symbols:")

    for symbol, count in sorted(symbols.items()):
        percentage = count / total_rows * 100

        print(
            f"  {symbol}: {count} "
            f"({percentage:.2f}%)"
        )


def main() -> None:
    for station_id, path in FILES.items():
        inspect_station(station_id, path)


if __name__ == "__main__":
    main()