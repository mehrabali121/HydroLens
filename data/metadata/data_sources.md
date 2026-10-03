# Data Sources and Provenance

## Project

River Rise Early-Warning Analysis Pipeline

This project analyzes historical water-level observations from monitoring
stations in the Saint John River basin.

The analysis is historical and is not an operational flood-warning or
emergency-response system.

## Primary Data Source

The primary data source is the Water Survey of Canada (WSC), part of
Environment and Climate Change Canada (ECCC).

WSC provides standardized hydrometric data including water-level
measurements from monitoring stations across Canada.

## Data Types Used

### Daily Historical Water-Level Data

Daily data provide one water-level value per day.

These data are intended to support:

- longer-term historical analysis
- station coverage analysis
- daily water-level changes
- missing-data analysis
- historical event analysis where daily resolution is sufficient

### Unit-Value Water-Level Data

Unit-value data provide higher-resolution water-level observations.

These data are intended to support:

- higher-resolution event analysis
- timing between upstream and downstream observations
- calculation of elapsed time between observations
- analysis of irregular sampling intervals

The project does not assume that unit observations occur at an exact
fixed interval. The timestamp of each observation will be used when
calculating elapsed time.

## Stations

The initial station set contains four stations along the Saint John River:

| Station ID | Station | Role |
|---|---|---|
| 01AF002 | Saint John River at Grand Falls | Upstream reference |
| 01AK003 | Saint John River at Fredericton | Downstream station |
| 01AO012 | Saint John River at Gagetown | Further downstream station |
| 01AP003 | Saint John River at Oak Point | Further downstream station |

The upstream/downstream relationship is based on the stations' positions
along the Saint John River.

The final analytical period will be determined after examining the actual
station-specific data coverage and data quality.

## Raw Sample Files

The repository currently contains small sample files used for development
and testing.

### Daily samples

- `grand_falls_2024_01.csv`
- `fredericton_2024_01.csv`
- `gagetown_2024_01.csv`
- `oak_point_2024_01.csv`

### Unit-value samples

- `grand_falls_unit_sample.csv`
- `fredericton_unit_sample.csv`
- `gagetown_unit_sample.csv`
- `oak_point_unit_sample.csv`

These files are development samples and do not represent the complete
historical dataset.

## Important Data Interpretation Notes

### Station-specific water-level references

Absolute water-level values should not be directly compared between
stations as if they shared the same reference elevation.

The analysis will primarily examine changes within each station and the
timing of changes between stations.

### Daily data

A daily water-level value represents the daily mean water level.

### Unit timestamps

Unit-value timestamps in the sample files use UTC timestamps with a `Z`
suffix.

The pipeline will preserve timezone information rather than treating
timestamps as timezone-naive values.

### Sampling interval

The sample unit-value files contain observations that are generally close
to five-minute intervals, but the project will not assume a fixed
five-minute interval.

Actual elapsed time will be calculated from consecutive timestamps.

### Approval status

The unit-value sample files contain provisional approval status.

The pipeline will preserve the original approval information rather than
silently treating provisional observations as finalized observations.

### Quality and symbols

The raw files contain fields such as symbols, qualifiers, and approval
information.

These fields will be preserved during ingestion so that data-quality
decisions can be made explicitly later.

## Data Preservation

Raw downloaded files are preserved in:

`data/raw/`

Raw files should not be manually edited after download.

Cleaning, validation, transformation, and analysis will occur in separate
pipeline stages.

## Reproducibility

The project will document:

1. the original data source
2. the station identifiers
3. the data types used
4. acquisition dates or periods where appropriate
5. transformations applied to the data
6. validation and cleaning decisions
7. analytical methods
8. software dependencies

The goal is for another person to understand how the analytical results
were produced from the source data.