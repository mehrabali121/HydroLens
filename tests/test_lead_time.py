import pandas as pd


def test_lead_time_calculation():
    upstream = pd.Timestamp("2020-01-01")
    downstream = pd.Timestamp("2020-01-02")

    lead_time = (downstream - upstream).days

    assert lead_time == 1
