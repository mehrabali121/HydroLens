# HydroLens

[![CI](https://github.com/mehrabali121/HydroLens/actions/workflows/ci.yml/badge.svg)](https://github.com/mehrabali121/HydroLens/actions/workflows/ci.yml)

**Historical River Rise & Lead-Time Analytics**

**Live Dashboard:** https://hydro-lens.streamlit.app/

HydroLens is a reproducible Python and SQL data pipeline with an interactive Streamlit dashboard. It looks at 14 years (2011 to 2024) of daily water-level data from four Water Survey of Canada stations on the Saint John River, from Grand Falls down to Oak Point, and asks: when the river rises sharply upstream, how often does a rise follow downstream, and how many days later?

This is an academic portfolio project. It is not an operational flood-warning, forecasting, or emergency-response system.

## How It Works

1. **Clean and store** about 19,550 daily readings in a SQLite database. Each reading is keyed by station and date, so duplicates are rejected.
2. **Detect rise events.** A day counts as a significant rise when the level goes up by at least that station's 95th percentile of daily rises. Each station gets its own threshold (0.62 m at Grand Falls, 0.52 m at Fredericton, 0.30 m at Gagetown, 0.23 m at Oak Point) because stations measure from different reference levels. Changes are only calculated between consecutive days, so gaps in the data never produce fake jumps. Result: 406 rise events.
3. **Group events into episodes.** Rises at the same station with no more than one quiet day between them are one episode. Result: 229 episodes.
4. **Match upstream to downstream.** For each Grand Falls episode, look for a downstream episode that starts 0 to 2 days later and pick the nearest one. Widening the window from 2 to 3 days added no new matches, while 5 to 10 days started pairing rises a week apart.
5. **Classify every unmatched case** before counting it. If downstream data was missing, or the downstream station was already rising, the case is left out of the match rate instead of being counted as "no rise."
6. **Calculate lead times** and export the results for the dashboard.

## Historical Analysis Results

There were 61 matched upstream/downstream episode pairs.

- 22 same-day, 32 one-day, and 7 two-day lead times
- Median lead time: 1 day (mean about 0.75 days)

Match rate = matched ÷ evaluable, where evaluable leaves out episodes with missing downstream data or where the downstream station was already rising.

| Downstream station | Matched | Evaluable | Match rate |
| --- | --- | --- | --- |
| `01AK003` Fredericton | 29 | 55 | 52.7% |
| `01AO012` Gagetown | 16 | 51 | 31.4% |
| `01AP003` Oak Point | 16 | 55 | 29.1% |

These are historical rates under this project's method. They are not forecasts, causal estimates, or guaranteed warning times.

## Interactive Dashboard

The dashboard reads its numbers from the pipeline's output in `results/`, so it always matches the latest pipeline run. It shows:

- overall analysis metrics
- per-station match counts, evaluable counts, and match rates
- a comparison of the downstream stations
- lead-time charts
- association outcomes for each station
- methodology and interpretation limits

Run it locally with:

```powershell
python -m streamlit run app.py
```

## Running the Project

Create and activate a virtual environment:

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
```

Install the pinned dependencies:

```powershell
python -m pip install --upgrade pip
pip install -r requirements.txt
```

Raw data files are not stored in Git. Download each station once:

```powershell
python scripts/acquire_wsc.py --station 01AF002 --start 2011-01-01 --end 2024-12-31
python scripts/acquire_wsc.py --station 01AK003 --start 2011-01-01 --end 2024-12-31
python scripts/acquire_wsc.py --station 01AO012 --start 2011-01-01 --end 2024-12-31
python scripts/acquire_wsc.py --station 01AP003 --start 2011-01-01 --end 2024-12-31
```

Run the full pipeline with one command:

```powershell
python run_pipeline.py
```

This runs every step in order, stops if any step fails, and copies the final results into `results/`. It can be run again at any time and gives the same results.

## Testing

HydroLens has 21 automated tests:

- 19 unit tests that call the project's own functions with small hand-made data. They cover daily change calculation (including gaps in the data and keeping stations separate), threshold calculation, rise detection, episode grouping, upstream/downstream matching, classification of missing data, and lead times.
- 1 test that checks the result files agree with each other
- 1 smoke test that checks the dashboard runs without errors

Run all tests with:

```powershell
python -m pytest -v
```

GitHub Actions runs the test suite on every push and pull request to `main`.

## Repository Structure

```text
HydroLens/
|-- .github/workflows/    GitHub Actions CI
|-- data/
|   |-- metadata/         Data source documentation
|   |-- raw/              Raw data (sample files only in Git)
|   `-- processed/        Generated data and SQLite database (not in Git)
|-- reports/figures/      Generated charts
|-- results/              Final result files the dashboard reads
|-- scripts/              Pipeline steps
|   `-- exploration/      Scripts used to explore the data and choose settings
|-- tests/                Automated tests
|-- app.py                Streamlit dashboard
|-- run_pipeline.py       Runs the full pipeline in order
|-- pytest.ini            Test settings
|-- requirements.txt      Pinned Python dependencies
`-- README.md
```

## Technologies

- Python 3.14
- pandas
- SQLite
- matplotlib
- Streamlit
- pytest
- Git, GitHub and GitHub Actions

## Limitations

The results depend on:

- data availability and missing observations
- each station's own behavior
- the 95th percentile rise threshold
- the episode grouping rule
- the 0 to 2 day matching window

A matched upstream/downstream pair shows that two rises happened close together in time. It does not prove that one caused the other, and past lead times are not guaranteed future warning times.