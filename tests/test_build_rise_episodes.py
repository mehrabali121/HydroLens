import pandas as pd

from scripts.build_rise_episodes import (
    build_episode_records,
    group_station_events,
)


def make_events(station_id, dates, rises):
    return pd.DataFrame(
        {
            "station_id": station_id,
            "trigger_date": pd.to_datetime(dates),
            "trigger_rise_m": rises,
        }
    )


def test_triggers_two_days_apart_stay_in_one_episode():
    # April 1 and April 3 have one quiet day between them.
    events = make_events("A", ["2020-04-01", "2020-04-03"], [0.5, 0.6])

    grouped = group_station_events(events)

    assert grouped["episode_number"].nunique() == 1


def test_triggers_three_days_apart_start_a_new_episode():
    events = make_events("A", ["2020-04-01", "2020-04-04"], [0.5, 0.6])

    grouped = group_station_events(events)

    assert grouped["episode_number"].nunique() == 2


def test_episode_record_has_correct_dates_count_and_largest_rise():
    events = make_events(
        "A",
        ["2020-04-01", "2020-04-02", "2020-04-04", "2020-05-01"],
        [0.5, 0.9, 0.6, 0.7],
    )

    episodes = build_episode_records(events, stations=["A"])

    assert len(episodes) == 2

    first = episodes.iloc[0]
    assert first["episode_id"] == "A_20200401"
    assert first["duration_days"] == 4
    assert first["trigger_count"] == 3
    assert first["largest_trigger_rise_m"] == 0.9
    assert first["largest_trigger_date"] == pd.Timestamp("2020-04-02")