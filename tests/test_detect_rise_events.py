import pandas as pd
import pytest

from scripts.detect_rise_events import (
    calculate_daily_changes,
    calculate_station_thresholds,
    detect_rise_events,
)


def make_observations(station_id, dates, levels):
    """Build a small table shaped like the daily_observations table."""
    return pd.DataFrame(
        {
            "station_id": station_id,
            "observation_date": pd.to_datetime(dates),
            "water_level_m": levels,
            "quality_symbol": "",
        }
    )


def test_daily_change_is_today_minus_yesterday():
    data = make_observations(
        "A",
        ["2020-04-01", "2020-04-02", "2020-04-03"],
        [1.0, 1.5, 1.2],
    )

    changes = calculate_daily_changes(data)

    # The first day has no "yesterday", so only 2 changes remain.
    assert len(changes) == 2
    assert changes["level_change_m"].round(2).tolist() == [0.5, -0.3]


def test_gap_in_dates_is_not_treated_as_one_day_change():
    # April 3 is missing, so April 2 -> April 4 is a 2-day gap.
    data = make_observations(
        "A",
        ["2020-04-01", "2020-04-02", "2020-04-04"],
        [1.0, 1.1, 3.0],
    )

    changes = calculate_daily_changes(data)

    assert changes["observation_date"].tolist() == [
        pd.Timestamp("2020-04-02")
    ]


def test_changes_are_not_mixed_between_stations():
    station_a = make_observations("A", ["2020-04-01", "2020-04-02"], [1.0, 1.2])
    station_b = make_observations("B", ["2020-04-01", "2020-04-02"], [9.0, 9.1])
    data = pd.concat([station_a, station_b], ignore_index=True)

    changes = calculate_daily_changes(data)

    # One change per station. Station B's first day must not be
    # compared with station A's last day.
    assert len(changes) == 2
    assert changes["level_change_m"].round(2).tolist() == [0.2, 0.1]


def test_threshold_uses_only_positive_rises():
    changes = pd.DataFrame(
        {
            "station_id": "A",
            "level_change_m": [-5.0, -2.0, 0.1, 0.2, 0.3, 0.4, 1.0],
        }
    )

    thresholds = calculate_station_thresholds(changes, stations=["A"])

    expected = pd.Series([0.1, 0.2, 0.3, 0.4, 1.0]).quantile(0.95)
    assert thresholds.loc[0, "threshold_m"] == pytest.approx(expected)
    assert thresholds.loc[0, "positive_rise_count"] == 5


def test_station_with_no_rises_raises_error():
    changes = pd.DataFrame(
        {"station_id": "A", "level_change_m": [-0.1, -0.2]}
    )

    with pytest.raises(ValueError):
        calculate_station_thresholds(changes, stations=["A"])


def test_only_rises_at_or_above_threshold_become_events():
    data = make_observations(
        "A",
        ["2020-04-01", "2020-04-02", "2020-04-03", "2020-04-04"],
        [1.0, 1.1, 1.6, 1.5],
    )
    changes = calculate_daily_changes(data)
    thresholds = pd.DataFrame({"station_id": ["A"], "threshold_m": [0.5]})

    events = detect_rise_events(changes, thresholds)

    # +0.1 is too small, +0.5 is exactly the threshold, -0.1 is a fall.
    assert len(events) == 1
    assert events.loc[0, "trigger_date"] == pd.Timestamp("2020-04-03")
    assert events.loc[0, "event_id"] == "A_20200403"