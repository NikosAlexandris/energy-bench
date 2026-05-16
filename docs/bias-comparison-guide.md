# Bias Comparison Guide

## Understanding the Bias Panel in `plot_metrics_overview()`

### What is the Bias Panel?

The **Bias panel** (middle panel in the metrics overview plot) shows the **percentage bias** between two time series, indicating systematic over- or under-estimation.

### Formula

```python
bias_pct = (mean_a / mean_b - 1.0) * 100.0
```

Where:
- `mean_a` = mean of series A (typically the indicator/ENTSO-E data)
- `mean_b` = mean of series B (typically the target/SFOE data)

### Interpretation

- **Positive bias (blue bars)**: Series A overestimates Series B
  - Example: +10% means A is 10% higher than B on average
- **Negative bias (red bars)**: Series A underestimates Series B
  - Example: -15% means A is 15% lower than B on average
- **Zero bias**: Perfect match in average levels

### Expected Values by Stage

| Stage | Expected Bias | Interpretation |
|-------|---------------|----------------|
| **Before** (ENTSO-E vs SFOE) | ±10-50% | Shows data quality issues |
| **After Scaling** | <1% | Daily totals match exactly |
| **After Benchmarking** | <0.1% | Near-perfect daily match |
| **After Advanced Scaling** | <0.5% | Good daily match with shape preservation |

---

## How to Compare Bias Before and After Adjustment

### 1. Before Adjustment: Original ENTSO-E vs SFOE Targets

This shows the initial bias in the raw ENTSO-E data:

```bash
# Compare all energy types at once (generates metrics CSV)
nrgbnc compare shape \
  --high-frequency-csv data/entsoe_hourly.csv \
  --low-frequency-csv data/sfoe_daily.csv \
  --start 2024-01-01 \
  --end 2024-12-31 \
  --output-csv output/metrics_entsoe_vs_sfoe_2024.csv

# Then visualize the bias
nrgbnc plot metrics \
  --metrics-csv output/metrics_entsoe_vs_sfoe_2024.csv \
  --output output/bias_before_adjustment_2024.png
```

**What you'll see:**
- **Bias panel** showing how much each energy type over/underestimates SFOE
- Likely significant bias (±10-50%) for most types
- Red bars = ENTSO-E underestimates SFOE
- Blue bars = ENTSO-E overestimates SFOE

---

### 2. After Adjustment: Compare Adjusted vs Target

#### Option A: Using Scaled Data

```bash
# First, scale the data (if not already done)
nrgbnc scale river \
  --high-frequency-csv data/entsoe_hourly.csv \
  --low-frequency-csv data/sfoe_daily.csv \
  --start 2024-01-01 \
  --end 2024-12-31 \
  --output-csv output/river_hourly_scaled_2024.csv

# Then compare scaled vs target
nrgbnc compare scaled-vs-target \
  --scaled-csv output/river_hourly_scaled_2024.csv \
  --target-csv data/sfoe_daily.csv \
  --variable river \
  --start 2024-01-01 \
  --end 2024-12-31 \
  --kind-of-csv scaled \
  --output-csv output/river_scaled_validation_2024.csv
```

#### Option B: Using Benchmarked Data

```bash
# First, benchmark the data (if not already done)
nrgbnc benchmark river \
  --high-frequency-csv data/entsoe_hourly.csv \
  --low-frequency-csv data/sfoe_daily.csv \
  --start 2024-01-01 \
  --end 2024-12-31 \
  --output-csv output/river_hourly_benchmarked_2024.csv

# Then compare benchmarked vs target
nrgbnc compare scaled-vs-target \
  --scaled-csv output/river_hourly_benchmarked_2024.csv \
  --target-csv data/sfoe_daily.csv \
  --variable river \
  --start 2024-01-01 \
  --end 2024-12-31 \
  --kind-of-csv benchmarked \
  --output-csv output/river_benchmarked_validation_2024.csv
```

**What you'll see:**
- Bias should be **near 0%** (typically <1%)
- MAE and RMSE showing remaining errors
- Validation that daily totals match SFOE targets

---

### 3. Before vs After Comparison: Show Improvement

This command compares original vs adjusted AND calculates bias improvement:

```bash
# Compare original vs scaled (shows improvement)
nrgbnc compare shape-scaled \
  --scaled-csv output/river_hourly_scaled_2024.csv \
  --target-csv data/sfoe_daily.csv \
  --variable river \
  --start 2024-01-01 \
  --end 2024-12-31 \
  --kind-of-csv scaled \
  --output-csv output/river_improvement_metrics_2024.csv
```

**Console output will show:**
```
📊 Comparison Summary for river_scaled:
   Original bias vs target: +15.23%
   Adjusted bias vs target: +0.02%
   Improvement: 15.21 percentage points
   Original MAE: 0.0234 GWh
   Adjusted MAE: 0.0012 GWh
   MAE reduction: 94.9%
```

---

### 4. Visualize Multiple Adjustments Together

To compare different adjustment methods side-by-side:

```bash
# Generate metrics for each method
nrgbnc compare scaled-vs-target \
  --scaled-csv output/river_hourly_scaled_2024.csv \
  --target-csv data/sfoe_daily.csv \
  --variable river \
  --start 2024-01-01 \
  --end 2024-12-31 \
  --kind-of-csv scaled \
  --category-name "river_scaled" \
  --output-csv output/river_scaled_metrics.csv

nrgbnc compare scaled-vs-target \
  --scaled-csv output/river_hourly_benchmarked_2024.csv \
  --target-csv data/sfoe_daily.csv \
  --variable river \
  --start 2024-01-01 \
  --end 2024-12-31 \
  --kind-of-csv benchmarked \
  --category-name "river_benchmarked" \
  --output-csv output/river_benchmarked_metrics.csv

# Combine CSVs manually or with pandas, then plot:
nrgbnc plot metrics \
  --metrics-csv output/combined_metrics.csv \
  --output output/adjustment_comparison_2024.png
```

---

## Key Parameters

- `--kind-of-csv`: Choose adjustment type
  - `scaled`: Simple daily scaling
  - `benchmarked`: Temporal disaggregation (Chow-Lin)
  - `scaled-per-day`: Advanced per-day scaling

- `--category-name`: Custom label for the comparison (useful when comparing multiple methods)

---

## Implementation Details

### Bias Calculation

The bias percentage is calculated in `compare/shape.py`:

```python
if "mean_a" in row and "mean_b" in row and row["mean_b"] not in (0, None):
    row["bias_pct"] = (row["mean_a"] / row["mean_b"] - 1.0) * 100.0
else:
    row["bias_pct"] = float("nan")
```

### Relationship with MBE (Mean Bias Error)

The `compare_series()` function also calculates `mbe`:

```python
"mbe": mbe(x, y),  # = (x - y).mean()
```

**Relationship:**
- `bias_pct` ≈ `(mbe / mean_b) * 100` when values are close
- `bias_pct` is a **relative** measure (percentage)
- `mbe` is an **absolute** measure (same units as data, e.g., GWh)

**Both are correct**, they just measure different aspects:
- Use `bias_pct` to understand relative systematic error (better for comparing across different scales)
- Use `mbe` to understand absolute systematic error (better for understanding actual magnitude)

---

## Troubleshooting

### Error: "TypeError: 'NoneType' object is not iterable"

This error occurred in earlier versions when `columns=None` was passed to `read_csv()`. It has been fixed in the current version by handling the `None` case explicitly.

If you encounter this error, make sure you're using the latest version of the code.

---

## Example Workflow

Here's a complete workflow for analyzing bias before and after adjustment:

```bash
# 1. Analyze original bias (all energy types)
nrgbnc compare shape \
  --high-frequency-csv ../data/ENTSOE/entsoe_hourly_2016_2025.csv \
  --low-frequency-csv ../data/SFOE/swissgrid_daily_production_2016_2025.csv \
  --start 2018-01-01 \
  --end 2024-12-31 \
  --output-csv output/metrics_original_2018_2024.csv

# 2. Visualize original bias
nrgbnc plot metrics \
  --metrics-csv output/metrics_original_2018_2024.csv \
  --output output/bias_original_2018_2024.png

# 3. Scale the river data
nrgbnc scale river \
  --high-frequency-csv ../data/ENTSOE/entsoe_hourly_2016_2025.csv \
  --low-frequency-csv ../data/SFOE/swissgrid_daily_production_2016_2025.csv \
  --start 2018-01-01 \
  --end 2024-12-31 \
  --output-csv output/river_hourly_scaled_2018_2024.csv

# 4. Compare scaled vs target
nrgbnc compare scaled-vs-target \
  --scaled-csv output/river_hourly_scaled_2018_2024.csv \
  --target-csv ../data/SFOE/swissgrid_daily_production_2016_2025.csv \
  --variable river \
  --start 2018-01-01 \
  --end 2024-12-31 \
  --kind-of-csv scaled \
  --output-csv output/river_scaled_validation_2018_2024.csv

# 5. Show improvement
nrgbnc compare shape-scaled \
  --scaled-csv output/river_hourly_scaled_2018_2024.csv \
  --target-csv ../data/SFOE/swissgrid_daily_production_2016_2025.csv \
  --variable river \
  --start 2018-01-01 \
  --end 2024-12-31 \
  --kind-of-csv scaled \
  --output-csv output/river_improvement_2018_2024.csv
```

The bias panel makes it immediately obvious which adjustment method works best for each energy type!
