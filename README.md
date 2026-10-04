# HydroLens

[![CI](https://github.com/mehrabali121/HydroLens/actions/workflows/ci.yml/badge.svg)](https://github.com/mehrabali121/HydroLens/actions/workflows/ci.yml)

**Historical River Rise & Lead-Time Analytics**

HydroLens is a reproducible Python and SQL data-analysis pipeline for investigating historical water-level rise events and upstream/downstream temporal relationships between hydrometric monitoring stations in the Saint John River basin.

The project detects historical water-level rise events, groups them into episodes, examines upstream/downstream temporal associations, and summarizes observed lead times in matched historical cases.

This is an academic portfolio project. It is not an operational flood-warning, forecasting, or emergency-response system.

## Project Status

The core historical analysis pipeline is implemented, including:

- hydrometric data acquisition and validation
- daily data cleaning and normalization
- SQLite storage and verification
- exploratory water-level analysis
- historical rise-event detection
- rise-episode construction
- upstream/downstream episode matching
- historical association classification
- lead-time calculation and summary
- historical backtesting
- visualization
- automated tests
- GitHub Actions continuous integration
- reproducible pinned Python dependencies

## Technologies

- Python 3.14
- pandas
- matplotlib
- SQLite
- pytest
- Git and GitHub
- GitHub Actions

## Important Interpretation

The analysis describes historical temporal associations in the available data.

A matched upstream/downstream event does not establish causation, and historical lead times should not be interpreted as guaranteed future warning times. Missing observations, station-specific behavior, event-definition choices, and the historical matching methodology all affect the results.

## Repository Structure

```text
HydroLens/
|-- .github/workflows/    GitHub Actions CI
|-- data/
|   |-- metadata/         Data-source documentation
|   |-- raw/              Raw and sample hydrometric data
|   `-- processed/        Generated cleaned data, database, and analysis outputs
|-- reports/
|   `-- figures/          Generated analysis visualizations
|-- scripts/              Data acquisition, validation, analysis, and visualization scripts
|-- tests/                Automated pytest tests
|-- requirements.txt      Pinned Python dependencies
`-- README.md             Project documentation
```

The repository tracks source code, tests, documentation, sample/reference data, and generated figures. Larger raw downloads and generated processed datasets, including the SQLite database, are excluded from Git and are intended to be recreated through the analysis pipeline.

## Reproducing the Environment

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

Verify the environment and run the automated tests:

```powershell
python -m pip check
python -m pytest -v
```

The project currently targets Python 3.14. Dependency versions are pinned in `requirements.txt`, and the same dependency file is used by the GitHub Actions CI workflow.

## Historical Analysis Results

The historical matching analysis identified 61 matched upstream/downstream rise-episode associations.

Observed lead times among these matched cases were:

- 22 same-day associations
- 32 one-day associations
- 7 two-day associations
- median lead time: 1 day
- mean lead time: approximately 0.75 days
- observed range: 0 to 2 days

Historical matched proportions differed by downstream station:

- `01AK003`: 29 of 59 evaluable upstream episodes matched (49.2%)
- `01AO012`: 16 of 55 evaluable upstream episodes matched (29.1%)
- `01AP003`: 16 of 58 evaluable upstream episodes matched (27.6%)

These statistics describe the historical matching methodology used in this project. They are not forecasts, causal estimates, or guaranteed future warning times.

## Visualizations

### Historical Association Outcomes

![Historical association outcomes](reports/figures/historical_association_outcomes.png)

Shows the historical association outcomes for each downstream station under the project's episode-matching methodology.

### Historical Lead-Time Distribution

![Historical lead-time distribution](reports/figures/historical_lead_time_distribution.png)

Shows the distribution of observed 0-, 1-, and 2-day lead times across the 61 matched historical associations.

### Lead Time by Downstream Station

![Lead time by downstream station](reports/figures/lead_time_by_downstream_station.png)

Compares the observed historical lead-time distributions across the three downstream stations.

### Historical Backtest Lag Distribution

![Historical backtest lag distribution](reports/figures/historical_backtest_lag_distribution.png)

Summarizes the observed lag distribution used to validate the historical matching and lead-time workflow.