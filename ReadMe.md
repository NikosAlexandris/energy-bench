## Terminology

Energy-Bench uses **source-agnostic terminology** to support any time series data sources, not just ENTSO-E and SFOE.

### Core Concepts

- **Indicator**: High-frequency time series to be adjusted (e.g., ENTSO-E hourly, Swissgrid 15-min, or any custom source)
- **Target**: Low-frequency reference values (e.g., SFOE daily, or any authoritative source)
- **Adjusted/Benchmarked**: Output after temporal disaggregation (hourly values that sum to daily targets)
- **Original**: Unadjusted indicator values
- **Scaled**: Output after simple scaling operations

### Naming Conventions

**Variables and parameters:**
- `*_series`: Actual pandas Series objects
- `*_field` / `*_fields`: Schema/column names
- `*_file`: Source file paths
- `indicator_*`: Related to high-frequency data
- `target_*`: Related to low-frequency reference data

**Standard parameter names:**

| Concept | Parameter Name | Example |
|---------|---------------|---------|
| Indicator CSV file | `indicator_csv` | `entsoe_hourly.csv` |
| Target CSV file | `target_csv` | `sfoe_daily.csv` |
| Adjusted CSV file | `adjusted_csv` | `river_benchmarked.csv` |
| Indicator time column | `indicator_time_column` | `"DateTime"` |
| Target time column | `target_time_column` | `"Date"` |
| Indicator columns | `indicator_fields` | `["Nuclear", "Solar"]` |
| Target columns | `target_fields` | `["Kernkraft", "Photovoltaik"]` |
| Benchmarked output | `benchmarked_column` | `"nuclear_benchmarked_gwh"` |
| Original values | `original_column` | `"nuclear_original_gwh"` |

### Source Provenance

All outputs include metadata tracking data sources:
- `indicator_source`: Name of indicator data source (e.g., "ENTSO-E", "Swissgrid", "CustomAPI")
- `target_source`: Name of target data source (e.g., "SFOE", "CustomReference")

This design allows the tool to work with any combination of high-frequency and low-frequency time series sources, making it extensible and reusable beyond the original Swiss electricity use case.

## Quick Start

### Benchmark Energy Type

```bash
# Benchmark river generation
nrgbnc benchmark river \
  --indicator-csv data/entsoe_hourly.csv \
  --target-csv data/sfoe_daily.csv \
  --start 2024-01-01 \
  --end 2024-12-31
```

### Compare Time Series

```bash
# Compare indicator vs target (shows why adjustment is needed)
nrgbnc compare series indicator target \
  --variable river \
  --indicator-csv data/entsoe_hourly.csv \
  --target-csv data/sfoe_daily.csv \
  --start 2024-01-01 \
  --end 2024-12-31

# Compare indicator vs adjusted (shows what changed)
nrgbnc compare series indicator adjusted \
  --variable river \
  --indicator-csv data/entsoe_hourly.csv \
  --adjusted-csv output/river/river_hourly_benchmarked_2024_2024.csv \
  --start 2024-01-01 \
  --end 2024-12-31

# Compare adjusted vs target (validates adjustment)
nrgbnc compare series adjusted target \
  --variable river \
  --adjusted-csv output/river/river_hourly_benchmarked_2024_2024.csv \
  --target-csv data/sfoe_daily.csv \
  --start 2024-01-01 \
  --end 2024-12-31
```

### Plot Comparisons

```bash
# Plot indicator vs target
nrgbnc plot compare indicator target \
  --variable river \
  --indicator-csv data/entsoe_hourly.csv \
  --target-csv data/sfoe_daily.csv \
  --start 2024-01-01 \
  --end 2024-12-31

# Plot indicator vs adjusted
nrgbnc plot compare indicator adjusted \
  --variable river \
  --indicator-csv data/entsoe_hourly.csv \
  --adjusted-csv output/river/river_hourly_benchmarked_2024_2024.csv \
  --start 2024-01-01 \
  --end 2024-12-31
```

For more examples, see `docs/unified-comparison-examples.md`.


## Registry of 

VARIABLES = {
    "water": {
        "label": "Water",
        "target_fields": ["Flusskraft", "Speicherkraft"],
        "indicator_fields": [
            "Hydro Run-of-river and poundage",
            "Hydro Water Reservoir",
            "Hydro Pumped Storage",
        ],
        "adjusted_field": "water_benchmarked_gwh",
        "original_field": "water_original_gwh",
        "output_filename": "benchmarked_hourly_water.csv",
        "kind": "aggregate",
    },
    ...
}

``` python
cfg["target_fields"] = cfg.get("target_fields", [])
cfg["indicator_fields"] = cfg.get("indicator_fields", [])
cfg["adjusted_field"] = cfg.get("adjusted_field", f"{key}_benchmarked_gwh")
cfg["original_field"] = cfg.get("original_field", f"{key}_original_gwh")
