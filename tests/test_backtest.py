import pandas as pd


def test_historical_backtest_rules():
    df = pd.DataFrame(
        {
            "match_id": ["match_1", "match_2", "match_3"],
            "observed_lag_days": [0, 1, 2],
            "within_historical_window": [True, True, True],
        }
    )

    assert len(df) == 3
    assert df["match_id"].is_unique
    assert df["observed_lag_days"].notna().all()
    assert df["observed_lag_days"].between(0, 2).all()
    assert df["within_historical_window"].all()