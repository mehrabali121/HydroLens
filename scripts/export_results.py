"""Copy the small final result files into results/ so the dashboard can use them.

data/processed/ is ignored by Git, so the deployed dashboard cannot see it.
results/ is tracked by Git.
"""

import shutil
from pathlib import Path


EVENTS_DIR = Path("data/processed/events")
RESULTS_DIR = Path("results")

FILES_TO_EXPORT = [
    "historical_association_summary.csv",
    "historical_lead_times.csv",
]


def main() -> None:
    RESULTS_DIR.mkdir(exist_ok=True)

    for file_name in FILES_TO_EXPORT:
        source = EVENTS_DIR / file_name

        if not source.exists():
            raise FileNotFoundError(
                f"{source} does not exist. Run the earlier pipeline steps first."
            )

        shutil.copy(source, RESULTS_DIR / file_name)
        print(f"Copied {source} -> {RESULTS_DIR / file_name}")


if __name__ == "__main__":
    main()