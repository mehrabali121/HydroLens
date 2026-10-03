import csv
from collections import Counter
from datetime import date
from pathlib import Path


RAW_DIR = Path("data/raw")

FILES = {
    "01AF002": RAW_DIR / "wsc_01AF002_daily_20000101_20251231.csv",
    "01AK003": RAW_DIR / "wsc_01AK003_daily_20000101_20251231.csv",
    "01AO012": RAW_DIR / "wsc_01AO012_daily_20000101_20251231.csv",
    "01AP003": RAW_DIR / "wsc_01AP003_daily_20000101_20251231.csv",
}

START_YEAR = 2011
END_YEAR = 2025


def inspect_station(station_id: str, path: Path) -> None:
    """Print yearly observation and quality statistics."""

    observations = Counter()
    symbols = Counter()

    with path.open("r", encoding="utf-8-sig", newline="") as file:
        reader = csv.DictReader(file)

        for row in reader:
            observation_date = date.fromisoformat(row["Date"])

            if START_YEAR <= observation_date.year <= END_YEAR:
                observations[observation_date.year] += 1

                symbol = row["Symbol/Symbole"].strip()

                if symbol:
                    symbols[(observation_date.year, symbol)] += 1

    print(f"\nStation: {station_id}")
    print(
        "Year | Expected | Observed | Missing | "
        "Coverage | A | E"
    )
    print("-" * 58)

    for year in range(START_YEAR, END_YEAR + 1):
        expected = (
            date(year + 1, 1, 1) - date(year, 1, 1)
        ).days

        observed = observations[year]
        missing = expected - observed
        coverage = observed / expected * 100

        partial = symbols[(year, "A")]
        estimated = symbols[(year, "E")]

        print(
            f"{year} | "
            f"{expected:8} | "
            f"{observed:8} | "
            f"{missing:7} | "
            f"{coverage:7.2f}% | "
            f"{partial:2} | "
            f"{estimated:2}"
        )


def main() -> None:
    for station_id, path in FILES.items():
        inspect_station(station_id, path)


if __name__ == "__main__":
    main()