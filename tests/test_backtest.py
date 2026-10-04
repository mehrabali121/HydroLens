from pathlib import Path

import pandas as pd


BACKTEST_PATH = Path("data/processed/events/historical_backtest_results.csv")


def test_historical_backtest_output():
    df = pd.read_csv(BACKTEST_PATH)

    assert len(df) == 61
    assert df["match_id"].is_unique
    assert df["observed_lag_days"].notna().all()
    assert df["observed_lag_days"].between(0, 2).all()
    assert df["within_historical_window"].all()
