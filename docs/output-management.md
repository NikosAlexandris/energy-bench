# Output Management

This document describes the centralized output management system in Energy-Bench.

## Overview

All output operations (CSV, PNG, TXT) are now handled through a centralized module: `energybench.io.output`. This ensures consistent file naming, directory structure, and reduces code duplication across commands.

## Directory Structure

Outputs are organized by variable (energy type) in subdirectories:

```
output/
├── river/
│   ├── river_hourly_benchmarked_2025.csv
│   ├── river_hourly_scaled_2025.csv
│   ├── river_original_vs_target_2025.png
│   └── river_before_vs_after_scaled_2025.png
├── nuclear/
│   ├── nuclear_hourly_benchmarked_2025.csv
│   └── nuclear_original_vs_target_2025.png
└── solar/
    └── solar_hourly_benchmarked_2025.csv
```

## Core Functions

### `save_dataframe()`

Saves pandas DataFrames to CSV with consistent formatting.

```python
from energybench.io.output import save_dataframe

save_dataframe(
    df=benchmarked_df,
    filename="river_hourly_benchmarked_2025.csv",
    output_dir=Path("output"),
    variable="river",  # Creates output/river/ subdirectory
    index=False,
)
# Output: 💾 CSV saved to output/river/river_hourly_benchmarked_2025.csv
```

**Parameters:**
- `df`: DataFrame to save
- `filename`: Output filename
- `output_dir`: Base output directory (default: "output")
- `variable`: Energy type for subdirectory (optional)
- `index`: Whether to write index (default: False)
- `date_format`: Format for datetime columns (default: "%Y-%m-%d %H:%M:%S")
- `**kwargs`: Additional arguments passed to `df.to_csv()`

### `save_figure()`

Saves matplotlib figures to PNG with consistent formatting.

```python
from energybench.io.output import save_figure
import matplotlib.pyplot as plt

fig, ax = plt.subplots()
ax.plot([1, 2, 3])

save_figure(
    fig=fig,
    filename="river_plot_2025.png",
    output_dir=Path("output"),
    variable="river",
    close_after=False,
)
# Output: 💾 Plot saved to output/river/river_plot_2025.png
```

**Parameters:**
- `fig`: Figure to save (if None, uses `plt.gcf()`)
- `filename`: Output filename
- `output_dir`: Base output directory (default: "output")
- `variable`: Energy type for subdirectory (optional)
- `dpi`: Resolution (default: 180)
- `bbox_inches`: Bounding box (default: "tight")
- `facecolor`: Background color (default: "white")
- `close_after`: Whether to close figure after saving (default: False)
- `**kwargs`: Additional arguments passed to `plt.savefig()`

### `save_text()`

Saves text content to file.

```python
from energybench.io.output import save_text

save_text(
    content="Summary statistics...",
    filename="river_summary_2025.txt",
    output_dir=Path("output"),
    variable="river",
)
# Output: 💾 Text saved to output/river/river_summary_2025.txt
```

**Parameters:**
- `content`: Text content to save
- `filename`: Output filename
- `output_dir`: Base output directory (default: "output")
- `variable`: Energy type for subdirectory (optional)
- `encoding`: Text encoding (default: "utf-8")

### `build_filename()`

Builds standardized filenames with optional temporal extent.

```python
from energybench.io.output import build_filename
import pandas as pd

# Single year
filename = build_filename(
    base_name="hourly_benchmarked",
    variable="river",
    start=pd.Timestamp("2025-01-01"),
    end=pd.Timestamp("2025-12-31"),
    suffix=".csv",
)
# Returns: "river_hourly_benchmarked_2025.csv"

# Multiple years
filename = build_filename(
    base_name="hourly_benchmarked",
    variable="river",
    start=pd.Timestamp("2024-01-01"),
    end=pd.Timestamp("2025-12-31"),
    suffix=".csv",
)
# Returns: "river_hourly_benchmarked_2024_2025.csv"
```

**Parameters:**
- `base_name`: Base filename (e.g., "hourly_benchmarked")
- `variable`: Energy type (optional)
- `start`: Start timestamp (optional)
- `end`: End timestamp (optional)
- `suffix`: File extension (default: ".csv")
- `include_variable_prefix`: Whether to prefix with variable name (default: True)

## Usage in Commands

### Benchmark Commands

All benchmark commands (`nuclear`, `river`, `solar`, `storage`, `thermal`, `water`, `wind`) use:

```python
from energybench.io.output import save_dataframe, build_filename

filename = build_filename(
    base_name="hourly_benchmarked",
    variable=variable,
    start=start,
    end=end,
    suffix=".csv",
)

save_dataframe(
    df=benchmarked_dataframe,
    filename=filename,
    output_dir=output_dir,
    variable=variable,
    index=False,
)
```

### Scale Commands

The `scale` command (with optional advanced flags) uses the same pattern:

```python
filename = build_filename(
    base_name="hourly_scaled",  # or "hourly_scaled_advanced"
    variable=variable,
    start=start,
    end=end,
    suffix=".csv",
)

save_dataframe(
    df=out,
    filename=filename,
    output_dir=output_dir,
    variable=variable,
    index=False,
)
```

### Plot Commands

Plot commands use `save_figure()`:

```python
from energybench.io.output import save_figure, build_filename

filename = build_filename(
    base_name="original_vs_target",
    variable=variable,
    start=start,
    end=end,
    suffix=".png",
)

save_figure(
    fig=figure,
    filename=filename,
    output_dir=output_directory,
    variable=variable,
    close_after=False,
)
```

### Compare and Validate Commands

These commands use `save_dataframe()` with optional variable subdirectories:

```python
save_dataframe(
    df=comparison_df,
    filename=output_csv,
    output_dir=output_csv.parent if output_csv.is_absolute() else Path("output"),
    variable=variable,  # or None for non-variable-specific outputs
    index=False,
)
```

## Benefits

1. **Consistency**: All outputs follow the same naming and directory conventions
2. **Maintainability**: Changes to output format only need to be made in one place
3. **Organization**: Variable-specific subdirectories keep outputs organized
4. **Flexibility**: Easy to change output directory via `--output-dir` parameter
5. **User Feedback**: Consistent "💾 saved to..." messages across all commands

## Migration Notes

The old pattern:
```python
cfg = get_variable_config(variable)
if start.year == end.year:
    temporal_extent = start.year
else:
    temporal_extent = f"{start.year}_{end.year}"
output_path = output_dir / Path(f"{cfg['output_filename']}_{temporal_extent}").with_suffix('.csv')
out.to_csv(output_path, index=False, date_format="%Y-%m-%d %H:%M:%S")
print(f"💾 Output written to {output_path}")
```

Has been replaced with:
```python
filename = build_filename(
    base_name="hourly_benchmarked",
    variable=variable,
    start=start,
    end=end,
    suffix=".csv",
)
save_dataframe(
    df=out,
    filename=filename,
    output_dir=output_dir,
    variable=variable,
    index=False,
)
```

This reduces ~8 lines to ~4 lines per command while adding the variable subdirectory feature.
