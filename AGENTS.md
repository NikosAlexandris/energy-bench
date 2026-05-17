# AGENTS.md

This file provides guidance to agents when working with code in this repository.

## Project Overview

**Energy-Bench** (command: `nrgbnc`) is a Python-based temporal disaggregation and benchmarking tool designed for Swiss electricity generation time series. The project was built for EDIH's Energy-Data Hackathon Challenge #2, focusing on estimating hourly energy production for Switzerland.

### Core Purpose

The tool reconciles high-frequency (hourly) electricity generation data from ENTSO-E with low-frequency (daily) target values from SFOE (Swiss Federal Office of Energy) using temporal disaggregation methods. This ensures that hourly estimates sum to match official daily totals while preserving the temporal patterns from high-frequency indicators.

### Main Technologies

- **Python 3.14+**: Modern Python with copy-on-write optimizations
- **pandas**: Primary data manipulation library
- **tempdisagg**: Temporal disaggregation models (Chow-Lin, ensemble methods)
- **cyclopts**: CLI framework with automatic help generation
- **matplotlib**: Visualization and plotting
- **polars/pyarrow**: Alternative data processing (supplementary)
- **uv**: Fast Python package manager for dependency management

### Architecture

The project follows a modular CLI architecture:

```
src/energybench/
├── cli.py              # Main CLI entrypoint with cyclopts
├── benchmark.py        # Core benchmarking logic
├── variables.py        # Energy type configuration registry
├── helpers.py          # Utility functions (sum_columns, prepare_dataframe)
├── read.py            # CSV reading utilities
├── commands/          # Subcommand implementations
│   ├── benchmark/     # Per-energy-type benchmark commands
│   ├── compare.py     # Compare different series
│   ├── plot.py        # Visualization commands
│   ├── scale.py       # Scaling operations
│   ├── validate.py    # Validation logic
│   ├── kalman.py      # Kalman filter operations
│   └── ...
└── check/             # Data quality checks
```

### Energy Types Supported

The tool handles seven energy types, each with specific ENTSO-E indicators and SFOE targets:

1. **Nuclear** (atomic): Kernkraft ↔ Nuclear
2. **Water** (aggregate): Flusskraft + Speicherkraft ↔ Hydro (Run-of-river, Reservoir, Pumped Storage)
3. **River** (atomic): Flusskraft ↔ Hydro Run-of-river and poundage
4. **Storage** (atomic): Speicherkraft ↔ Hydro Water Reservoir + Pumped Storage
5. **Solar** (atomic): Photovoltaik ↔ Solar
6. **Wind** (aggregate): Wind ↔ Wind Onshore + Offshore
7. **Thermal** (aggregate): Thermische Erzeugung ↔ Fossil Gas, Coal, Oil, Waste, Other

Configuration for each type is centralized in `variables.py` using the `VARIABLES` registry.

## Building and Running

### Installation

```bash
# Install dependencies using uv (recommended)
uv sync

# Or using pip
pip install -e .
```

### Running the CLI

The main command is `nrgbnc` (or `python -m energybench.cli`):

```bash
# Show help
nrgbnc --help

# List available variables/energy types
nrgbnc list

# Benchmark a specific energy type
nrgbnc benchmark river \
  --indicator-csv data/entsoe_hourly.csv \
  --target-csv data/sfoe_daily.csv \
  --start 2024-01-01 \
  --end 2024-12-31

# Compare any two series (new unified interface)
nrgbnc compare series indicator target \
  --variable river \
  --indicator-csv data/entsoe_hourly.csv \
  --target-csv data/sfoe_daily.csv \
  --start 2024-01-01 \
  --end 2024-12-31

# Plot comparison
nrgbnc plot compare indicator adjusted \
  --variable river \
  --indicator-csv data/entsoe_hourly.csv \
  --adjusted-csv output/river_benchmarked.csv \
  --start 2024-01-01 \
  --end 2024-12-31

# Validate output
nrgbnc validate --help
```

### Key Commands

**Unified Comparison Interface (New):**
- **`compare series <series1> <series2>`**: Compare any two series (indicator, adjusted, target)
- **`plot compare <series1> <series2>`**: Plot comparison between any two series

Valid comparisons:
- `indicator vs target`: Shows why adjustment is needed
- `indicator vs adjusted`: Shows what changed during adjustment  
- `adjusted vs target`: Validates adjustment worked correctly

- **`benchmark <energy-type>`**: Run temporal disaggregation for a specific energy type
- **`scale`**: Scale hourly data to match targets
- **`compare`**: Compare different time series (ENTSO-E vs SFOE, original vs benchmarked)
- **`plot`**: Generate visualizations
- **`validate`**: Validate benchmarked results against targets
- **`kalman`**: Apply Kalman filtering
- **`plausibility`**: Check data plausibility
- **`assemble`**: Combine multiple benchmarked series

### Testing

```bash
# Run tests (if available)
pytest

# Type checking
mypy src/energybench

# Linting
ruff check src/energybench
```

## Development Conventions

### Code Style

- **Line length**: 100 characters (configured in `pyproject.toml`)
- **Target version**: Python 3.14
- **Linter**: Ruff for fast linting and formatting
- **Type hints**: Encouraged, with mypy for type checking

### Terminology and Naming Conventions

The codebase uses specific terminology to distinguish between data sources and roles:

**Preferred terminology** (source-agnostic):

- `*_series`: Actual pandas Series objects
- `*_field` / `*_fields`: Schema/column names
- `*_file`: Source file paths
- `target`: Low-frequency reference data (e.g., SFOE daily totals, or any authoritative source)
- `indicator`: High-frequency data to be adjusted (e.g., ENTSO-E hourly, Swissgrid 15-min, or any high-frequency source)
- `adjusted` / `benchmarked`: Output after temporal disaggregation
- `original`: Unadjusted indicator values

**Important Design Principle**: The tool is designed to be **source-agnostic**. While the current implementation primarily uses ENTSO-E (indicator) and SFOE (target) data, the architecture and terminology support any high-frequency indicator and low-frequency target sources. Always use generic terms (`indicator`, `target`) rather than source-specific names (`entsoe`, `sfoe`) in core logic.

**Variable configuration keys**:
- `target_type` / `target_types_present`: Target source column names (e.g., SFOE columns)
- `indicator_type` / `indicator_types_present`: Indicator source column names (e.g., ENTSO-E columns)
- `output_column`: Name for benchmarked output
- `original_column`: Name for original indicator values
- `kind`: Either "atomic" (single type) or "aggregate" (sum of multiple types)
- `indicator_source`: Default indicator data source name
- `target_source`: Default target data source name

### Data Processing Patterns

1. **Reading data**: Use `read_csv()` from `energybench.read` with proper time column specification
2. **Summing columns**: Use `sum_columns()` helper which handles missing columns gracefully
3. **Preparing for disaggregation**: Use `prepare_dataframe()` to convert to tempdisagg format
4. **Configuration**: Always retrieve energy type config via `get_variable_config(variable)`

### Pandas Optimizations

The codebase enables pandas performance features:
```python
pd.options.mode.copy_on_write = True  # Faster pandas operations
pd.options.future.infer_string = True  # Better string handling
```

### Error Handling

- Missing columns trigger warnings but processing continues with available columns
- Strict mode in `get_variable_config()` validates that required columns exist
- Use descriptive error messages referencing expected vs. actual column names

### Adding New Energy Types

To add a new energy type:

1. Add configuration to `VARIABLES` dict in `variables.py`
2. Specify `entsoe_types` (indicator columns) and `sfoe_types` (target columns)
3. Set `kind` to "atomic" or "aggregate"
4. Create a command module in `commands/benchmark/` if needed
5. Register in `cli.py`

### Output Conventions

- Benchmarked outputs include metadata columns: `date`, `hour`, `month`, `variable`, `indicator_source`, `target_source`, `kind`
- Default output directory: `output/`
- Filename pattern: `{variable}_hourly_benchmarked_{start}_{end}.csv`
- Plots saved with descriptive names indicating comparison type and date range

## Project Context

This tool addresses the challenge of creating consistent hourly electricity generation estimates for Switzerland by:

1. Using official daily totals (SFOE) as constraints
2. Leveraging hourly patterns from ENTSO-E transparency platform
3. Applying statistical temporal disaggregation methods (Chow-Lin, ensemble)
4. Validating results against known totals and plausibility checks

The `archived/` directory contains previous iterations and validation results. The `output/` directory stores current benchmarked series, metrics, and visualizations.
