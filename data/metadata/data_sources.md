# Data Sources and Provenance

## Project

River Rise Analysis is a reproducible historical analysis of water-level observations from hydrometric monitoring stations in the Saint John River basin.

The project examines historical water-level rises and temporal relationships between upstream and downstream stations.

This is an academic portfolio project. It is not an operational flood-warning, forecasting, or emergency-response system.

## Primary Data Source

The primary data source is the Water Survey of Canada (WSC), part of Environment and Climate Change Canada (ECCC).

The project uses hydrometric water-level observations obtained for selected monitoring stations in the Saint John River basin.

## Stations

The analysis uses four stations along the Saint John River:

| Station ID | Station | Analytical Role |
|---|---|---|
| `01AF002` | Saint John River at Grand Falls | Upstream reference |
| `01AK003` | Saint John River at Fredericton | Downstream station |
| `01AO012` | Saint John River at Gagetown | Further downstream station |
| `01AP003` | Saint John River at Oak Point | Further downstream station |

The upstream/downstream interpretation is based on the stations' positions along the river.

## Data Used in the Historical Analysis

Daily historical water-level observations are used for the implemented historical analysis pipeline.

The pipeline uses these observations to examine:

- station-specific historical coverage
- missing observations and data quality
- daily water-level changes
- significant historical rise events
- multi-day rise episodes
- temporal relationships between upstream and downstream episodes
- observed lead times in matched historical cases

The repository also contains small unit-value sample files retained as reference and development data. The implemented historical lead-time results documented in the project are based on the daily-data analysis pipeline.

## Repository Data

Small reference and sample datasets are tracked under:

```text
data/raw/
```

Tracked daily samples are organized by station:

```text
data/raw/daily/<station_id>/
```

Tracked unit-value samples are organized by station:

```text
data/raw/unit/<station_id>/
```

Larger historical downloads are excluded from Git.

Generated cleaned datasets, event-analysis outputs, and the SQLite database are also excluded from Git and are intended to be recreated through the analysis pipeline.

## Data Interpretation

### Station-specific water-level references

Absolute water-level values should not be directly compared between stations as though all stations share the same reference elevation.

The analysis therefore focuses primarily on changes within individual stations and temporal relationships between station-specific rise episodes.

### Missing observations

Historical data availability varies by station and period.

The matching analysis distinguishes evaluable cases from cases with insufficient downstream data so that missing observations are not silently treated as evidence that no downstream rise occurred.

### Historical associations

A downstream rise occurring within the project's matching window after an upstream rise is treated as a historical temporal association.

This does not establish that the upstream rise caused the downstream rise.

### Lead time

Historical lead time is calculated only for matched upstream/downstream rise episodes.

For the implemented daily analysis, lead time is the difference in calendar days between the upstream episode start date and the matched downstream episode start date.

These observed historical lead times are descriptive results and should not be interpreted as guaranteed future warning times.

## Data Preservation

Raw downloaded data are stored under:

```text
data/raw/
```

Raw source files should not be manually edited after acquisition.

Cleaning, normalization, validation, database loading, event detection, matching, and analysis are performed in separate pipeline stages.

## Reproducibility

The repository documents and preserves:

1. the source of the hydrometric data
2. station identifiers and analytical roles
3. representative sample data
4. data-cleaning and validation code
5. historical event and episode definitions
6. upstream/downstream matching logic
7. lead-time and backtesting code
8. generated portfolio visualizations
9. automated tests
10. pinned Python dependencies
11. continuous-integration configuration

The goal is to make the analytical workflow understandable, reviewable, and reproducible without presenting the project as an operational forecasting system.