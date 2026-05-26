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

The project follows a modular CLI architecture with clear separation between CLI and library code:

```
src/energybench/
├── cli/                # All CLI commands
│   ├── app.py         # Main CLI entrypoint with cyclopts
│   ├── benchmark/     # Per-energy-type benchmark commands
│   ├── compare/       # Compare commands (unified interface)
│   ├── plot/          # Visualization commands
│   ├── scale/         # Scaling operations
│   ├── validate/      # Validation commands
│   ├── analyse/       # Analysis commands
│   └── ...
├── core/              # Core library utilities
│   ├── configuration.py  # Energy type registry (VARIABLES)
│   ├── utilities.py      # Helper functions (sum_columns, prepare_dataframe)
│   ├── metrics.py        # Comparison metrics
│   ├── shape.py          # Shape analysis
│   ├── validation.py     # Validation logic
│   ├── analyse/          # Bias detection and visualization
│   ├── check/            # Plausibility checks
│   ├── describe/         # Statistical descriptions
│   ├── print/            # Metrics printing
│   ├── compare/          # Compare utilities
│   ├── plots/            # Plot utilities
│   └── validate/         # Validation utilities
├── models/            # Algorithms
│   ├── benchmarking.py   # Core benchmarking logic
│   ├── disaggregation.py # Temporal disaggregation
│   ├── scaling.py        # Scaling methods
│   └── kalman.py         # Kalman filtering
└── io/                # I/O operations
    ├── input.py
    ├── output.py
    └── fetch.py
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

Configuration for each type is centralized in `core/configuration.py` using the `VARIABLES` registry.

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

---

## Session History

### Goal
Develop a Python CLI tool for benchmarking energy time series, with emphasis on temporal disaggregation, visualization, bias detection, and validation against Swissgrid data.

### Key Decisions
- Single `scale` command replaces `simple`/`advanced` split — global scaling factor rejected as too crude for multi-year data.
- UKF is 1D hourly filter + daily reconciliation, not 24D — proved mathematically equivalent to `scale`, kept only as experimental comparison.
- **Chow-Lin (`tempdisagg`) is the only genuinely different method** — it models the indicator-target relationship via regression, not proportional scaling. Improvement is ~3% on MAE vs Swissgrid.
- **Regime-splicing approach rejected** — methods are too similar (scale ≡ UKF, benchmark only marginally different) for per-regime method selection to add value.
- **Plot column/factor overrides** are optional (`None`/`1.0` by default) — when omitted, falls through to existing config-based lookup. Fully backward-compatible.
- `--variable` cannot be restricted to a cyclopts enum because `--variable all` also needs to be valid; help text lists valid values, runtime validation via `get_variable_config()`.
- **Atomic types only** for Swissgrid validation: exclude `water` (aggregate of river+storage) to avoid triple-counting. Remaining 6 types sum to 1.07× Swissgrid (7% over) — a reasonable data-source methodology difference.
- **Totals discovery uses glob patterns**, not filename construction — avoids mismatch between query date range and file's date range.

### Commands
| Subcommand | Behavior |
|---|---|
| `plot compare <s1> <s2>` | Original: compare two series for one/all variables |
| `plot compare totals --auto` | **NEW**: sum all atomic-type CSVs from `auto_dir/{var}/` and compare vs a reference CSV |
| `plot compare totals --total-csv` | **NEW**: compare a single pre-computed total CSV vs reference |

### Swissgrid Data
- Located at `data/clean/EnergieUebersichtCH-{year}_production_wide.csv`
- Columns: `ds` (datetime), per-canton, total (`Summe produzierte Energie...`), grid feed-in
- Units: kWh → use `--reference-factor 1e-6` for GWh
- Total = sum of cantons + foreign territories
- Our 6-type atomic sum = 1.07× Swissgrid (7% overcount = methodology difference)

### Relevant Files
- `src/energybench/cli/plot/unified.py`: `plot_totals_comparison()`, `_find_component_csv()`, `_get_component_column()`, `_ATOMIC_VARIABLES`
- `src/energybench/cli/plot/app.py`: `compare_app` with default + totals subcommand

---

## Session Changelog

### 2026-05-21: Docs cleanup & compare_methods bugfix

**Bugfix** (`scripts/compare_methods.py`):
- Scatter plot crashed with `"x and y must be the same size"` because Swissgrid 2024 has 8785 hours (includes hour 0 of 2025-01-01) while indicator totals have 8784. Fixed by aligning on common index via `index.intersection()`.
- Changed scatter from 1-week window to full year per the user's request. Updated title and filename from `scatter_week.png` to `scatter_full_year.png`.

**`docs/understanding_the_data.md` cleaned** (surgical, no pipeline removal):
- Removed dangling empty footnote `[^]`
- Removed conflicting platform footnote definitions (`[^1]`-`[^4]`, `[^16]`, `[^17]`) embedded in the Swissgrid section that overrode the bottom References section
- Fixed broken markdown link: `(opendata.swiss)[opendata.swiss]` → `[opendata.swiss](url)`
- Removed two "___Stuff to clean-up___" banners
- Cleaned Benchmarking section: removed 6 empty subsections (Prepare/Benchmarking/Evaluate with raw `..`/`...` placeholders and corrupted `xtxt` math), replaced with 2-line intro
- Renamed "Further" → "Combining Speicherkraft types"
- Renamed "Unsorted..." → "Daily comparison with scaling factors"
- Removed 12 dangling `[^7]`, `[^9]`, `[^10]` editorial footnote markers in Methods section
- Updated TOC to match all renamed/removed sections
- All 22 Miller commands, 2 curl downloads, 12 code blocks, and all data tables preserved intact
