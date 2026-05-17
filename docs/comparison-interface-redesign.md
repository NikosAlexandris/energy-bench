# Comparison Interface Redesign

## Current State (Messy)

### Compare Commands
```bash
nrgbnc compare types          # Compare energy types
nrgbnc compare shape          # Compare shape (original vs target)
nrgbnc compare scaled-vs-target  # Validate scaled vs target
```

### Plot Commands
```bash
nrgbnc plot original-vs-target   # Plot original vs target
nrgbnc plot before-vs-after      # Plot original vs adjusted
nrgbnc plot after-vs-target      # Plot adjusted vs target (called "difference")
nrgbnc plot metrics              # Plot comparison metrics
nrgbnc plot assembled            # Plot assembled series
```

**Problems:**
- Inconsistent naming (before/after vs original/adjusted)
- Unclear what each command does
- No unified interface for comparing series
- "difference" is confusing name for "after-vs-target"

---

## Proposed Clean Interface

### Core Concept: Three Series Types

1. **Original** - Unadjusted indicator data (e.g., ENTSO-E hourly)
2. **Adjusted** - After benchmarking/scaling (reconciled to targets)
3. **Target** - Reference data (e.g., SFOE daily totals)

### Unified Compare Command

```bash
# Compare any two series with metrics
nrgbnc compare <series1> <series2> [options]

# Where series1/series2 can be:
#   - original    (indicator before adjustment)
#   - adjusted    (after benchmarking/scaling)
#   - target      (reference data)
```

### Examples

```bash
# Compare original indicator vs target (shows why adjustment needed)
nrgbnc compare original target \
  --variable river \
  --indicator-csv data/entsoe_hourly.csv \
  --target-csv data/sfoe_daily.csv \
  --start 2024-01-01 \
  --end 2024-12-31 \
  --output-csv output/river_original_vs_target_metrics.csv \
  --plot output/river_original_vs_target.png

# Compare original vs adjusted (shows what changed)
nrgbnc compare original adjusted \
  --variable river \
  --adjusted-csv output/river_hourly_benchmarked.csv \
  --indicator-csv data/entsoe_hourly.csv \
  --start 2024-01-01 \
  --end 2024-12-31 \
  --output-csv output/river_original_vs_adjusted_metrics.csv \
  --plot output/river_original_vs_adjusted.png

# Compare adjusted vs target (validates adjustment worked)
nrgbnc compare adjusted target \
  --variable river \
  --adjusted-csv output/river_hourly_benchmarked.csv \
  --target-csv data/sfoe_daily.csv \
  --start 2024-01-01 \
  --end 2024-12-31 \
  --output-csv output/river_adjusted_vs_target_metrics.csv \
  --plot output/river_adjusted_vs_target.png
```

---

## Implementation Plan

### Phase 1: Create Unified Compare Command

**New file:** `src/energybench/commands/compare/unified.py`

```python
def compare_series_unified(
    series1: Literal["original", "adjusted", "target"],
    series2: Literal["original", "adjusted", "target"],
    variable: str,
    start: Timestamp,
    end: Timestamp,
    # File paths (only required ones needed based on series1/series2)
    indicator_csv: Path | None = None,
    adjusted_csv: Path | None = None,
    target_csv: Path | None = None,
    # Optional parameters
    kind_of_adjusted: KindOfCSV = KindOfCSV.benchmarked,
    output_csv: Path | None = None,
    plot_output: Path | None = None,
    indicator_time_column: str = "DateTime",
    target_time_column: str = "Date",
    adjusted_time_column: str = "DateTime",
) -> pd.DataFrame:
    """
    Compare any two series: original, adjusted, or target.
    
    Valid combinations:
    - original vs target: Shows why adjustment is needed
    - original vs adjusted: Shows what changed during adjustment
    - adjusted vs target: Validates adjustment worked correctly
    
    Args:
        series1: First series to compare ("original", "adjusted", "target")
        series2: Second series to compare ("original", "adjusted", "target")
        variable: Energy type (e.g., "river", "nuclear", "solar")
        start: Start timestamp
        end: End timestamp
        indicator_csv: Path to indicator CSV (required if series1 or series2 is "original")
        adjusted_csv: Path to adjusted CSV (required if series1 or series2 is "adjusted")
        target_csv: Path to target CSV (required if series1 or series2 is "target")
        kind_of_adjusted: Type of adjusted series (benchmarked, scaled, scaled-per-day)
        output_csv: Optional path to save comparison metrics
        plot_output: Optional path to save comparison plot
        
    Returns:
        DataFrame with comparison metrics
        
    Examples:
        >>> # Compare original vs target
        >>> metrics = compare_series_unified(
        ...     series1="original",
        ...     series2="target",
        ...     variable="river",
        ...     indicator_csv=Path("data/entsoe.csv"),
        ...     target_csv=Path("data/sfoe.csv"),
        ...     start=pd.Timestamp("2024-01-01"),
        ...     end=pd.Timestamp("2024-12-31"),
        ... )
    """
    # Validate inputs
    if series1 == series2:
        raise ValueError(f"Cannot compare series with itself: {series1}")
    
    required_files = {
        "original": ("indicator_csv", indicator_csv),
        "adjusted": ("adjusted_csv", adjusted_csv),
        "target": ("target_csv", target_csv),
    }
    
    for series_name in [series1, series2]:
        param_name, param_value = required_files[series_name]
        if param_value is None:
            raise ValueError(
                f"--{param_name.replace('_', '-')} is required when comparing '{series_name}'"
            )
    
    # Load series based on type
    cfg = get_variable_config(variable)
    
    def load_series(series_type: str) -> pd.Series:
        if series_type == "original":
            df = read_csv(indicator_csv, start, end, indicator_time_column)
            return sum_columns(df, cfg["indicator_types"], "original")
        
        elif series_type == "adjusted":
            df = pd.read_csv(adjusted_csv, parse_dates=[adjusted_time_column])
            df = df.set_index(adjusted_time_column).loc[start:end]
            col = {
                KindOfCSV.benchmarked: cfg["benchmarked_column"],
                KindOfCSV.scaled: cfg["scaled_column"],
                KindOfCSV.scaled_per_day: cfg["scaled_advanced_column"],
            }[kind_of_adjusted]
            return df[col].rename("adjusted")
        
        elif series_type == "target":
            df = read_csv(target_csv, start, end, target_time_column)
            return sum_columns(df, cfg["target_types"], "target")
    
    # Load both series
    s1 = load_series(series1)
    s2 = load_series(series2)
    
    # Aggregate to daily for comparison
    s1_daily = s1.resample("D").sum()
    s2_daily = s2.resample("D").sum()
    
    # Calculate metrics
    from energybench.core.metrics import compare_series
    metrics = compare_series(s1_daily, s2_daily)
    
    # Build output row
    row = {
        "comparison": f"{series1}_vs_{series2}",
        "variable": variable,
        "start": start,
        "end": end,
        **metrics.to_dict(),
    }
    
    # Print results
    print(f"\n📊 Comparison: {series1.upper()} vs {series2.upper()}")
    print(f"   Variable: {variable}")
    print(f"   Period: {start.date()} to {end.date()}")
    print(f"\n   Metrics:")
    print(f"     Pearson correlation: {metrics.pearson:.4f}")
    print(f"     MAE: {metrics.mae:.4f} GWh")
    print(f"     RMSE: {metrics.rmse:.4f} GWh")
    print(f"     Bias: {metrics.mbe:+.4f} GWh")
    
    # Save metrics if requested
    if output_csv:
        df = pd.DataFrame([row])
        save_dataframe(df, output_csv, output_csv.parent, variable, index=False)
        print(f"\n💾 Metrics saved to: {output_csv}")
    
    # Generate plot if requested
    if plot_output:
        from energybench.core.plots.difference import plot_series_difference
        fig = plot_series_difference(
            benchmarked_series=s1_daily,
            target_series=s2_daily,
            benchmarked_data_source=series1.capitalize(),
            target_data_source=series2.capitalize(),
            electricity_generation_type=cfg["label"],
            frequency="Daily",
            benchmarked_series_label=series1.capitalize(),
            target_series_label=series2.capitalize(),
            units="GWh",
            xlabel="Time",
        )
        save_figure(fig, plot_output, plot_output.parent, variable, close_after=True)
        print(f"📊 Plot saved to: {plot_output}")
    
    return pd.DataFrame([row])
```

### Phase 2: Update Compare App

**Update:** `src/energybench/commands/compare/app.py`

```python
from cyclopts import App
from energybench.commands.compare.unified import compare_series_unified
from energybench.commands.compare.types import compare_types

compare_app = App(
    name="compare",
    help="Compare time series: original indicator, adjusted, and target",
)

# New unified interface
compare_app.command(
    name="series",
    help="Compare any two series: original, adjusted, or target",
)(compare_series_unified)

# Keep specialized commands
compare_app.command(
    name="types",
    help="Compare energy types between indicator and target sources",
)(compare_types)

# Deprecate old commands (keep for backward compatibility)
from energybench.commands.compare.series import compare_series_shape
from energybench.commands.compare.scaled_vs_target import compare_scaled_vs_target

compare_app.command(
    name="shape",
    help="[DEPRECATED] Use 'compare series original target' instead",
)(compare_series_shape)

compare_app.command(
    name="scaled-vs-target",
    help="[DEPRECATED] Use 'compare series adjusted target' instead",
)(compare_scaled_vs_target)
```

### Phase 3: Simplify Plot Commands

**Update:** `src/energybench/commands/plot/app.py`

```python
from cyclopts import App
from energybench.commands.plot.unified import plot_comparison

plot_app = App(
    name="plot",
    help="Plot comparisons between original, adjusted, and target series",
)

# New unified interface
plot_app.command(
    name="compare",
    help="Plot comparison between any two series",
)(plot_comparison)

# Keep specialized commands
plot_app.command(
    name="metrics",
    help="Plot comparison metrics from CSV",
)(plot_comparison_metrics)

plot_app.command(
    name="assembled",
    help="Plot assembled multi-variable series",
)(plot_assembled)

# Deprecate old commands (keep for backward compatibility)
plot_app.command(
    name="original-vs-target",
    help="[DEPRECATED] Use 'plot compare original target' instead",
)(plot_original_vs_target)

plot_app.command(
    name="before-vs-after",
    help="[DEPRECATED] Use 'plot compare original adjusted' instead",
)(plot_before_vs_after)

plot_app.command(
    name="after-vs-target",
    help="[DEPRECATED] Use 'plot compare adjusted target' instead",
)(plot_difference)
```

---

## Migration Guide

### Old Commands → New Commands

```bash
# OLD: Compare original vs target
nrgbnc compare shape \
  --high-frequency-csv data/entsoe.csv \
  --low-frequency-csv data/sfoe.csv

# NEW: Compare original vs target
nrgbnc compare series original target \
  --indicator-csv data/entsoe.csv \
  --target-csv data/sfoe.csv

# OLD: Validate scaled vs target
nrgbnc compare scaled-vs-target \
  --scaled-csv output/river_scaled.csv \
  --target-csv data/sfoe.csv

# NEW: Compare adjusted vs target
nrgbnc compare series adjusted target \
  --adjusted-csv output/river_scaled.csv \
  --target-csv data/sfoe.csv \
  --kind-of-adjusted scaled

# OLD: Plot original vs target
nrgbnc plot original-vs-target \
  --original-high-frequency-csv data/entsoe.csv \
  --target-low-frequency-csv data/sfoe.csv

# NEW: Plot original vs target
nrgbnc compare series original target \
  --indicator-csv data/entsoe.csv \
  --target-csv data/sfoe.csv \
  --plot output/river_original_vs_target.png

# OLD: Plot before vs after
nrgbnc plot before-vs-after \
  --after-csv output/river_benchmarked.csv

# NEW: Plot original vs adjusted
nrgbnc compare series original adjusted \
  --indicator-csv data/entsoe.csv \
  --adjusted-csv output/river_benchmarked.csv \
  --plot output/river_original_vs_adjusted.png
```

---

## Benefits

1. **Consistency**: Single interface for all comparisons
2. **Clarity**: Clear naming (original/adjusted/target)
3. **Flexibility**: Compare any two series
4. **Simplicity**: One command instead of many
5. **Discoverability**: Easy to understand what's possible
6. **Backward Compatible**: Old commands still work (deprecated)

---

## Implementation Checklist

- [ ] Create `commands/compare/unified.py` with `compare_series_unified()`
- [ ] Create `commands/plot/unified.py` with `plot_comparison()`
- [ ] Update `commands/compare/app.py` to use new interface
- [ ] Update `commands/plot/app.py` to use new interface
- [ ] Add deprecation warnings to old commands
- [ ] Update documentation with new examples
- [ ] Create migration guide for users
- [ ] Test all comparison combinations
- [ ] Update AGENTS.md with new interface

---

## Future Enhancements

### Multi-Series Comparison

```bash
# Compare all three series at once
nrgbnc compare all \
  --variable river \
  --indicator-csv data/entsoe.csv \
  --adjusted-csv output/river_benchmarked.csv \
  --target-csv data/sfoe.csv \
  --output-csv output/river_all_comparisons.csv \
  --plot output/river_all_comparisons.png
```

### Shape Analysis

```bash
# Analyze intraday shape patterns
nrgbnc compare shape \
  --series1 original \
  --series2 target \
  --variable river \
  --indicator-csv data/entsoe.csv \
  --target-csv data/sfoe.csv \
  --analyze-intraday-patterns
```

### Batch Comparison

```bash
# Compare multiple variables at once
nrgbnc compare batch \
  --variables river storage solar \
  --indicator-csv data/entsoe.csv \
  --target-csv data/sfoe.csv \
  --output-dir output/comparisons/
```
