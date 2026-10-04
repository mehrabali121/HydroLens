import pandas as pd
import pytest

from scripts.classify_historical_associations import classify_records

NO_CANDIDATE = "no_candidate_within_window"


def test_each_record_gets_the_right_class():
    matches = pd.DataFrame(
        {
            "match_id": ["m1", "m2", "m3", "m4"],
            "match_status": ["matched", NO_CANDIDATE, NO_CANDIDATE, NO_CANDIDATE],
        }
    )
    availability = pd.DataFrame(
        {
            "match_id": ["m1", "m2", "m3", "m4"],
            "availability_status": [
                "matched",
                "insufficient_data",
                "evaluable_no_candidate",
                "evaluable_no_candidate",
            ],
        }
    )
    unmatched = pd.DataFrame(
        {
            "match_id": ["m1", "m2", "m3", "m4"],
            "window_result": [
                None,
                None,
                "significant_rise_during_existing_episode",
                "no_significant_rise",
            ],
        }
    )

    result = classify_records(matches, availability, unmatched)

    assert result["association_class"].tolist() == [
        "matched",
        "insufficient_data",
        "pre_existing_episode",
        "no_candidate",
    ]


def test_missing_data_is_never_counted_as_no_rise():
    # Even if the window shows nothing, missing data must win.
    matches = pd.DataFrame({"match_id": ["m1"], "match_status": [NO_CANDIDATE]})
    availability = pd.DataFrame(
        {"match_id": ["m1"], "availability_status": ["insufficient_data"]}
    )
    unmatched = pd.DataFrame(
        {"match_id": ["m1"], "window_result": ["no_significant_rise"]}
    )

    result = classify_records(matches, availability, unmatched)

    assert result.loc[0, "association_class"] == "insufficient_data"


def test_record_without_availability_raises_error():
    matches = pd.DataFrame({"match_id": ["m1"], "match_status": [NO_CANDIDATE]})
    availability = pd.DataFrame(
        {"match_id": ["other"], "availability_status": ["insufficient_data"]}
    )
    unmatched = pd.DataFrame({"match_id": ["m1"], "window_result": [None]})

    with pytest.raises(ValueError):
        classify_records(matches, availability, unmatched)