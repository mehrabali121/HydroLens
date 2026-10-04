from pathlib import Path

import pandas as pd


RESULTS_DIR = Path(__file__).resolve().parent.parent / "results"


def test_result_files_agree_with_each_other():
    summary = pd.read_csv(RESULTS_DIR / "historical_association_summary.csv")
    lead_times = pd.read_csv(RESULTS_DIR / "historical_lead_times.csv")

    # Every matched episode in the summary has exactly one lead time.
    assert summary["matched_episodes"].sum() == len(lead_times)

    # Matched can never be more than the number of evaluable episodes.
    assert (summary["matched_episodes"] <= summary["primary_match_evaluable"]).all()

    # All lead times are inside the 0-2 day matching window.
    assert lead_times["lead_time_days"].between(0, 2).all()