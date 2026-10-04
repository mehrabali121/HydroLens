import pandas as pd
import pytest

from scripts.analyze_lead_times import calculate_lead_times


def make_match_table(statuses, upstream_starts, downstream_starts):
    count = len(statuses)
    return pd.DataFrame(
        {
            "match_id": [f"m{i}" for i in range(count)],
            "match_status": statuses,
            "upstream_episode_id": "up",
            "upstream_station_id": "UP",
            "upstream_start_date": upstream_starts,
            "downstream_episode_id": "down",
            "downstream_station_id": "DOWN",
            "downstream_start_date": downstream_starts,
            "relationship": "follow_up",
        }
    )


def test_lead_time_is_days_between_episode_starts():
    table = make_match_table(
        ["matched", "matched"],
        ["2020-04-10", "2020-12-31"],
        ["2020-04-12", "2021-01-01"],
    )

    result = calculate_lead_times(table)

    # The second case crosses into a new year.
    assert result["lead_time_days"].tolist() == [2, 1]


def test_unmatched_rows_are_left_out():
    table = make_match_table(
        ["matched", "no_candidate_within_window"],
        ["2020-04-10", "2020-05-01"],
        ["2020-04-10", None],
    )

    result = calculate_lead_times(table)

    assert result["match_id"].tolist() == ["m0"]


def test_lead_time_outside_window_raises_error():
    table = make_match_table(["matched"], ["2020-04-10"], ["2020-04-15"])

    with pytest.raises(ValueError):
        calculate_lead_times(table)