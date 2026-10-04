from pathlib import Path

import pandas as pd
import streamlit as st


PROJECT_ROOT = Path(__file__).resolve().parent
FIGURES_DIR = PROJECT_ROOT / "reports" / "figures"


STATIONS = pd.DataFrame(
    [
        {
            "station_id": "01AF002",
            "location": "Grand Falls",
            "role": "Upstream reference",
        },
        {
            "station_id": "01AK003",
            "location": "Fredericton",
            "role": "Downstream",
        },
        {
            "station_id": "01AO012",
            "location": "Gagetown",
            "role": "Further downstream",
        },
        {
            "station_id": "01AP003",
            "location": "Oak Point",
            "role": "Further downstream",
        },
    ]
)


RESULTS_DIR = PROJECT_ROOT / "results"


@st.cache_data
def load_lead_times() -> pd.DataFrame:
    """Load one row per matched episode, made by the pipeline."""
    return pd.read_csv(RESULTS_DIR / "historical_lead_times.csv")


@st.cache_data
def load_station_results() -> pd.DataFrame:
    """Build the per-station table from the pipeline's result files."""
    summary = pd.read_csv(
        RESULTS_DIR / "historical_association_summary.csv"
    )
    lead_times = load_lead_times()

    results = pd.DataFrame(
        {
            "station_id": summary["downstream_station_id"],
            "matched": summary["matched_episodes"],
            "evaluable": summary["primary_match_evaluable"],
        }
    )

    results["matched_percent"] = (
        results["matched"] / results["evaluable"] * 100
    )

    lead_stats = (
        lead_times.groupby("downstream_station_id")["lead_time_days"]
        .agg(["mean", "median"])
        .rename(
            columns={
                "mean": "mean_lead_time",
                "median": "median_lead_time",
            }
        )
    )

    results = results.merge(
        lead_stats,
        left_on="station_id",
        right_index=True,
        how="left",
    )

    results = results.merge(
        STATIONS[["station_id", "location"]],
        on="station_id",
        how="left",
    )

    return results


LEAD_TIMES = load_lead_times()
STATION_RESULTS = load_station_results()


st.set_page_config(
    page_title="HydroLens",
    page_icon="🌊",
    layout="wide",
    initial_sidebar_state="expanded",
)


st.title("🌊 HydroLens")
st.subheader("Historical River Rise & Lead-Time Analytics")

st.markdown(
    """
HydroLens is a reproducible Python and SQL analytics project for exploring
historical water-level rise events and upstream/downstream temporal
relationships between hydrometric monitoring stations in the
**Saint John River basin**.
"""
)

st.info(
    "HydroLens analyzes historical observations. It is not an operational "
    "flood-warning, forecasting, or emergency-response system."
)


st.sidebar.header("Explore HydroLens")

selected_station = st.sidebar.selectbox(
    "Downstream station",
    STATION_RESULTS["station_id"],
    format_func=lambda station_id: (
        f"{station_id} — "
        f"{STATION_RESULTS.loc[STATION_RESULTS['station_id'] == station_id, 'location'].iloc[0]}"
    ),
)

st.sidebar.markdown(
    """
Use the station selector to explore historical matching and lead-time
statistics for each downstream monitoring station.
"""
)

st.sidebar.divider()

st.sidebar.caption(
    "Historical analytics only — not operational flood guidance."
)


st.divider()

st.header("Historical Analysis at a Glance")

col1, col2, col3, col4 = st.columns(4)

lead_days = LEAD_TIMES["lead_time_days"]

with col1:
    st.metric("Stations Analyzed", len(STATIONS))

with col2:
    st.metric("Matched Associations", len(LEAD_TIMES))

with col3:
    st.metric("Median Lead Time", f"{lead_days.median():.0f} day")

with col4:
    st.metric(
        "Observed Range",
        f"{lead_days.min()}–{lead_days.max()} days",
    )


st.divider()

st.header("Explore a Downstream Station")

selected = STATION_RESULTS.loc[
    STATION_RESULTS["station_id"] == selected_station
].iloc[0]

st.subheader(f"{selected['station_id']} — {selected['location']}")

station_col1, station_col2, station_col3, station_col4 = st.columns(4)

with station_col1:
    st.metric(
        "Matched Episodes",
        f"{int(selected['matched'])}",
    )

with station_col2:
    st.metric(
        "Evaluable Episodes",
        f"{int(selected['evaluable'])}",
    )

with station_col3:
    st.metric(
        "Historical Matched Proportion",
        f"{selected['matched_percent']:.1f}%",
    )

with station_col4:
    st.metric(
        "Median Lead Time",
        f"{selected['median_lead_time']:.0f} day",
    )

st.caption(
    "Evaluable episodes leave out cases where downstream data was "
    "missing or the downstream station was already rising. "
    "Matched proportion = matched episodes / evaluable episodes. "
    "It is a historical rate, not a forecast probability."
)


st.divider()

st.header("Compare Downstream Stations")

comparison_metric = st.radio(
    "Comparison metric",
    [
        "Historical matched proportion",
        "Matched episode count",
        "Mean observed lead time",
    ],
    horizontal=True,
)

if comparison_metric == "Historical matched proportion":
    comparison_data = STATION_RESULTS.set_index("station_id")[
        ["matched_percent"]
    ].rename(columns={"matched_percent": "Matched proportion (%)"})

    st.bar_chart(
        comparison_data,
        y_label="Percent",
    )

elif comparison_metric == "Matched episode count":
    comparison_data = STATION_RESULTS.set_index("station_id")[
        ["matched"]
    ].rename(columns={"matched": "Matched episodes"})

    st.bar_chart(
        comparison_data,
        y_label="Episodes",
    )

else:
    comparison_data = STATION_RESULTS.set_index("station_id")[
        ["mean_lead_time"]
    ].rename(columns={"mean_lead_time": "Mean lead time (days)"})

    st.bar_chart(
        comparison_data,
        y_label="Days",
    )

st.caption(
    "Station-level comparisons summarize historical results under the "
    "project's matching methodology."
)


st.divider()

st.header("Station Network")

st.dataframe(
    STATIONS,
    hide_index=True,
    width="stretch",
)


st.divider()

st.header("Historical Lead-Time Analysis")

lead_time_figure = FIGURES_DIR / "historical_lead_time_distribution.png"
station_lead_time_figure = FIGURES_DIR / "lead_time_by_downstream_station.png"

lead_col1, lead_col2 = st.columns(2)

with lead_col1:
    st.subheader("Overall Distribution")

    if lead_time_figure.exists():
        st.image(
            str(lead_time_figure),
            caption=(
                f"Observed lead times among {len(LEAD_TIMES)} matched "
                "historical upstream/downstream rise-episode associations."
            ),
            width="stretch",
        )
    else:
        st.warning(
            "The historical lead-time visualization is unavailable."
        )

with lead_col2:
    st.subheader("By Downstream Station")

    if station_lead_time_figure.exists():
        st.image(
            str(station_lead_time_figure),
            caption=(
                "Comparison of observed historical lead-time distributions "
                "across the three downstream stations."
            ),
            width="stretch",
        )
    else:
        st.warning(
            "The station lead-time visualization is unavailable."
        )


st.divider()

st.header("Association Outcomes")

association_figure = FIGURES_DIR / "historical_association_outcomes.png"

if association_figure.exists():
    st.image(
        str(association_figure),
        caption=(
            "Historical outcomes for each downstream station under "
            "the episode-matching methodology."
        ),
        width="stretch",
    )
else:
    st.warning(
        "The historical association-outcomes figure is unavailable."
    )


st.divider()

st.header("Methodology & Interpretation")

method_col, interpretation_col = st.columns(2)

with method_col:
    st.subheader("Historical methodology")
    st.markdown(
        """
1. Acquire and validate hydrometric observations.
2. Clean and normalize daily station data.
3. Detect significant historical water-level rises.
4. Group related rises into episodes.
5. Match downstream episodes occurring 0–2 days after upstream episodes.
6. Calculate observed lead times for matched historical cases.
"""
    )

with interpretation_col:
    st.subheader("Interpretation limits")
    st.markdown(
        """
- Temporal association does not establish causation.
- Historical lead time is not a guaranteed future warning time.
- Missing observations can affect whether an episode is evaluable.
- Station-specific behavior affects historical matching results.
- HydroLens does not generate operational flood forecasts.
"""
    )


st.divider()

st.caption(
    "HydroLens • Python • pandas • SQLite • matplotlib • pytest • "
    "Streamlit • GitHub Actions"
)