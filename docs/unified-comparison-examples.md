# Unified Comparison Interface - Usage Examples

## Overview

The new unified interface provides a single, consistent way to compare any two series:
- **indicator**: Original high-frequency data (e.g., ENTSO-E hourly)
- **adjusted**: After benchmarking/scaling (reconciled to targets)
- **target**: Low-frequency reference data (e.g., SFOE daily)

## Command Structure

```bash
# Compare with metrics
nrgbnc compare series <series1> <series2> --variable <type> --start <date> --end <date> [options]

# Plot comparison
nrgbnc plot compare <series1> <series2> --variable <type> --start <date> --end <date> [options]
```

## Common Use Cases

### 1. Compare Indicator vs Target (Why adjustment is needed)

Shows the bias and differences between original indicator data and target totals.

```bash
# Generate metrics
nrgbnc compare series indicator target \
  --variable river \
  --indicator-csv data/entsoe_hourly.csv \
  --target-csv data/sfoe_daily.csv \
  --start 2024-01-01 \
  --end 2024-12-31 \
  --output-csv output/river/river_indicator_vs_target_metrics.csv

# Generate plot
nrgbnc plot compare indicator target \
  --variable river \
  --indicator-csv data/entsoe_hourly.csv \
  --target-csv data/sfoe_daily.csv \
  --start 2024-01-01 \
  --end 2024-12-31 \
  --output-file output/river/river_indicator_vs_target.png
```

### 2. Compare Indicator vs Adjusted (What changed)

Shows the impact of benchmarking/scaling on the original data.

```bash
# Generate metrics
nrgbnc compare series indicator adjusted \
  --variable river \
  --indicator-csv data/entsoe_hourly.csv \
  --adjusted-csv output/river/river_hourly_benchmarked_2024_2024.csv \
  --start 2024-01-01 \
  --end 2024-12-31 \
  --output-csv output/river/river_indicator_vs_adjusted_metrics.csv

# Generate plot
nrgbnc plot compare indicator adjusted \
  --variable river \
  --indicator-csv data/entsoe_hourly.csv \
  --adjusted-csv output/river/river_hourly_benchmarked_2024_2024.csv \
  --start 2024-01-01 \
  --end 2024-12-31 \
  --output-file output/river/river_indicator_vs_adjusted.png
```

### 3. Compare Adjusted vs Target (Validate adjustment)

Validates that the adjustment successfully reconciled to target totals.

```bash
# Generate metrics
nrgbnc compare series adjusted target \
  --variable river \
  --adjusted-csv output/river/river_hourly_benchmarked_2024_2024.csv \
  --target-csv data/sfoe_daily.csv \
  --start 2024-01-01 \
  --end 2024-12-31 \
  --output-csv output/river/river_adjusted_vs_target_metrics.csv

# Generate plot
nrgbnc plot compare adjusted target \
  --variable river \
  --adjusted-csv output/river/river_hourly_benchmarked_2024_2024.csv \
  --target-csv data/sfoe_daily.csv \
  --start 2024-01-01 \
  --end 2024-12-31 \
  --output-file output/river/river_adjusted_vs_target.png
```

## Advanced Options

### Compare Different Adjustment Methods

```bash
# Compare scaled vs target
nrgbnc compare series adjusted target \
  --variable river \
  --adjusted-csv output/river/river_hourly_scaled_2024_2024.csv \
  --target-csv data/sfoe_daily.csv \
  --kind-of-adjusted scaled \
  --start 2024-01-01 \
  --end 2024-12-31

# Compare scaled-per-day vs target
nrgbnc compare series adjusted target \
  --variable river \
  --adjusted-csv output/river/river_hourly_scaled_advanced_2024_2024.csv \
  --target-csv data/sfoe_daily.csv \
  --kind-of-adjusted scaled-per-day \
  --start 2024-01-01 \
  --end 2024-12-31
```

### Custom Labels and Output

```bash
# Plot with custom labels
nrgbnc plot compare indicator adjusted \
  --variable river \
  --indicator-csv data/entsoe_hourly.csv \
  --adjusted-csv output/river/river_hourly_benchmarked_2024_2024.csv \
  --start 2024-01-01 \
  --end 2024-12-31 \
  --series1-label "ENTSO-E Original" \
  --series2-label "Chow-Lin Benchmarked" \
  --output-file output/river/custom_comparison.png
```

## Output Interpretation

### Metrics CSV Columns

- `comparison`: Type of comparison (e.g., "indicator_vs_target")
- `variable`: Energy type
- `start`, `end`: Time period
- `n_days`: Number of days compared
- `pearson`, `spearman`, `cosine`: Correlation metrics
- `mbe`: Mean Bias Error (systematic over/under estimation)
- `mae`: Mean Absolute Error
- `rmse`: Root Mean Square Error
- `nrmse_mean`: Normalized RMSE (%)
- `smape`: Symmetric Mean Absolute Percentage Error (%)
- `bias_pct`: Bias as percentage
- `mean_a`, `mean_b`: Mean values of both series
- `std_a`, `std_b`: Standard deviations
- `sum_a`, `sum_b`: Total sums
- `best_lag`, `best_lag_corr`: Temporal lag analysis

### Key Metrics to Watch

**For indicator vs target:**
- High `bias_pct` → Systematic over/under estimation
- Low `pearson` → Poor temporal correlation
- High `mae`/`rmse` → Large absolute differences

**For adjusted vs target:**
- `bias_pct` should be near 0% (successful reconciliation)
- `mae`/`rmse` should be minimal
- `pearson` should be high (preserved temporal patterns)

**For indicator vs adjusted:**
- Shows magnitude of adjustment
- High correlation → Adjustment preserved patterns
- Low correlation → Significant reshaping occurred

## Migration from Old Commands

```bash
# OLD: nrgbnc compare shape
nrgbnc compare series indicator target \
  --indicator-csv ... --target-csv ...

# OLD: nrgbnc compare scaled-vs-target
nrgbnc compare series adjusted target \
  --adjusted-csv ... --target-csv ... --kind-of-adjusted scaled

# OLD: nrgbnc plot original-vs-target
nrgbnc plot compare indicator target \
  --indicator-csv ... --target-csv ...

# OLD: nrgbnc plot before-vs-after
nrgbnc plot compare indicator adjusted \
  --indicator-csv ... --adjusted-csv ...

# OLD: nrgbnc plot after-vs-target
nrgbnc plot compare adjusted target \
  --adjusted-csv ... --target-csv ...
```

## Batch Processing Example

```bash
#!/bin/bash
# Compare all energy types for 2024

VARIABLES="nuclear river storage solar wind"
START="2024-01-01"
END="2024-12-31"

for var in $VARIABLES; do
  echo "Processing $var..."
  
  # Indicator vs target
  nrgbnc compare series indicator target \
    --variable $var \
    --indicator-csv data/entsoe_hourly.csv \
    --target-csv data/sfoe_daily.csv \
    --start $START --end $END \
    --output-csv output/$var/${var}_indicator_vs_target.csv
  
  # Adjusted vs target
  nrgbnc compare series adjusted target \
    --variable $var \
    --adjusted-csv output/$var/${var}_hourly_benchmarked_2024_2024.csv \
    --target-csv data/sfoe_daily.csv \
    --start $START --end $END \
    --output-csv output/$var/${var}_adjusted_vs_target.csv
done
```
