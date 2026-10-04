import pandas as pd

from scripts.match_rise_episodes import (
    find_candidates,
    select_nearest_candidates,
)


def make_episodes(station_id, starts, ends):
    starts = pd.to_datetime(starts)
    return pd.DataFrame(
        {
            "episode_id": [f"{station_id}_{d:%Y%m%d}" for d in starts],
            "station_id": station_id,
            "episode_start": starts,
            "episode_end": pd.to_datetime(ends),
        }
    )


def test_only_downstream_starts_0_to_2_days_later_are_candidates():
    upstream = make_episodes("UP", ["2020-04-10"], ["2020-04-11"])
    downstream = make_episodes(
        "DOWN",
        ["2020-04-09", "2020-04-10", "2020-04-12", "2020-04-13"],
        ["2020-04-09", "2020-04-10", "2020-04-12", "2020-04-13"],
    )

    candidates = find_candidates(upstream, downstream)

    # -1 day (before upstream) and +3 days are outside the window.
    assert sorted(candidates["start_lag_days"].tolist()) == [0, 2]


def test_relationship_is_overlap_or_follow_up():
    upstream = make_episodes("UP", ["2020-04-10"], ["2020-04-11"])
    downstream = make_episodes(
        "DOWN",
        ["2020-04-11", "2020-04-12"],
        ["2020-04-11", "2020-04-12"],
    )

    candidates = find_candidates(upstream, downstream)
    by_lag = dict(zip(candidates["start_lag_days"], candidates["relationship"]))

    # Starts while upstream is still rising -> overlap.
    assert by_lag[1] == "overlap"
    # Starts after upstream ended -> follow_up.
    assert by_lag[2] == "follow_up"


def test_nearest_candidate_is_selected():
    upstream = make_episodes("UP", ["2020-04-10"], ["2020-04-10"])
    downstream = make_episodes(
        "DOWN",
        ["2020-04-11", "2020-04-12"],
        ["2020-04-11", "2020-04-12"],
    )

    candidates = find_candidates(upstream, downstream)
    selected = select_nearest_candidates(candidates)

    assert len(selected) == 1
    assert selected.loc[0, "downstream_episode_id"] == "DOWN_20200411"


def test_no_candidates_gives_empty_result():
    upstream = make_episodes("UP", ["2020-04-10"], ["2020-04-10"])
    downstream = make_episodes("DOWN", ["2020-06-01"], ["2020-06-01"])

    candidates = find_candidates(upstream, downstream)
    selected = select_nearest_candidates(candidates)

    assert selected.empty