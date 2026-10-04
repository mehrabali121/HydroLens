# River Rise Analysis

A reproducible Python and SQL historical analysis of water-level relationships between hydrometric monitoring stations in the Saint John River basin.

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
