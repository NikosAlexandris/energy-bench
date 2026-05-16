# Temporal Disaggregation Methodology for Swiss Energy Data

## Overview

This document describes the methodology for creating hourly electricity generation time series that:
1. **Preserve temporal patterns** from ENTSO-E hourly data (incomplete but has shape)
2. **Match official totals** from SFOE daily data (complete and accurate)
3. **Handle data quality issues** through adaptive method selection

This is a **temporal disaggregation** problem where we reconcile high-frequency indicators with low-frequency constraints.

---

## The Challenge

### Data Sources

**ENTSO-E Transparency Platform (Hourly)**
- **Pros**: Hourly granularity, captures temporal patterns
- **Cons**: Systematically incomplete (especially 2016-2024)
- **Coverage**: ~4-12% of actual generation for hydro run-of-river (2016-2024)
- **Quality**: Improves to ~100% by 2025

**SFOE (Swiss Federal Office of Energy) (Daily)**
- **Pros**: Official statistics, complete and accurate
- **Cons**: Only daily totals, no hourly breakdown
- **Coverage**: 100% of Swiss generation
- **Quality**: High (ground truth)

**SwissGrid 15-minute Total Production**
- **Pros**: High temporal resolution, complete totals
- **Cons**: Not broken down by energy type
- **Coverage**: Total production only
- **Quality**: High

### The Problem

Given:
- Incomplete hourly indicators (ENTSO-E)
- Complete daily targets (SFOE)
- Complete 15-minute totals (SwissGrid)

Create:
- Complete hourly series by energy type
- That preserves temporal patterns
- And matches official daily totals

---

## Available Methods

### 1. Simple Scaling

**Formula:**
```python
factor = daily_target / daily_sum_of_hourly
scaled_hourly = hourly * factor
```

**When to use:**
- Data quality is good (ratio ~1-3x)
- Simple proportional adjustment needed
- Fast processing required

**Limitations:**
- Fails with extreme factors (>10x)
- Assumes hourly pattern is correct
- No statistical modeling

**Command:**
```bash
nrgbnc scale river \
  --high-frequency-csv data/entsoe_hourly.csv \
  --low-frequency-csv data/sfoe_daily.csv \
  --start 2025-01-01 \
  --end 2026-12-31
```

### 2. Advanced Scaling (Per-Day)

**Features:**
- Applies constraints (min_value, preserve_zeros)
- Redistributes remainder across non-zero hours
- Skips days with very small sums

**When to use:**
- Need to preserve zeros
- Want to enforce minimum values
- Data has some quality issues

**Command:**
```bash
nrgbnc scale advanced river \
  --high-frequency-csv data/entsoe_hourly.csv \
  --low-frequency-csv data/sfoe_daily.csv \
  --start 2025-01-01 \
  --end 2026-12-31 \
  --min-value 0.0 \
  --preserve-zeros true \
  --min-daily-sum 1.5
```

### 3. Benchmarking (Chow-Lin)

**Method:**
- Statistical temporal disaggregation
- Models relationship between high and low frequency
- Handles systematic bias through regression
- Preserves temporal patterns while matching targets

**When to use:**
- Systematic bias in indicators (2016-2024)
- Need statistical rigor
- Want smooth temporal patterns

**Command:**
```bash
nrgbnc benchmark river \
  --high-frequency-csv data/entsoe_hourly.csv \
  --low-frequency-csv data/sfoe_daily.csv \
  --start 2016-01-01 \
  --end 2024-12-31
```

### 4. Kalman Filtering

**Method:**
- State-space model
- Combines multiple indicators
- Adaptive estimation
- Handles missing data

**When to use:**
- Multiple indicators available
- Need adaptive smoothing
- Want to combine different data sources

**Command:**
```bash
nrgbnc kalman river \
  --high-frequency-csv data/entsoe_hourly.csv \
  --low-frequency-csv data/sfoe_daily.csv \
  --start 2016-01-01 \
  --end 2024-12-31
```

---

## Adaptive Method Selection Strategy

### Recommended Approach by Period

**2016-2017 (Very Poor Data Quality)**
- **Method**: Benchmarking (Chow-Lin)
- **Reason**: Handles 20-27x systematic bias
- **Alternative**: Skip scaling, use original with warning

**2018-2024 (Poor Data Quality)**
- **Method**: Benchmarking (Chow-Lin)
- **Reason**: Handles 8-11x systematic bias
- **Alternative**: Advanced scaling with min_daily_sum=2.0

**2025-2026 (Good Data Quality)**
- **Method**: Simple or Advanced Scaling
- **Reason**: Data is nearly complete (1.1x ratio)
- **Alternative**: Benchmarking for consistency

### Assemble Workflow

Create a composite series using the best method for each period:

**Step 1: Process each period separately**
```bash
# 2016-2024: Use benchmarking
nrgbnc benchmark river \
  --start 2016-01-01 \
  --end 2024-12-31 \
  --output-dir output/historical

# 2025-2026: Use scaling
nrgbnc scale advanced river \
  --start 2025-01-01 \
  --end 2026-12-31 \
  --output-dir output/recent
```

**Step 2: Create assembly configuration**
```yaml
# config/river_assembly.yaml
start: 2016-01-01
end: 2026-12-31
time_column: DateTime
output_name: river_assembled_gwh

components:
  - name: river_historical
    csv: output/historical/river_hourly_benchmarked_2016_2024.csv
    column: river_benchmarked_gwh
    start: 2016-01-01
    end: 2024-12-31
    
  - name: river_recent
    csv: output/recent/river_hourly_scaled_advanced_2025_2026.csv
    column: river_scaled_per_day_gwh
    start: 2025-01-01
    end: 2026-12-31
```

**Step 3: Assemble**
```bash
nrgbnc assemble \
  --config config/river_assembly.yaml \
  --output output/river_hourly_assembled_2016_2026.csv
```

---

## Using 15-Minute Total Production Data

The 15-minute total production data can be used in several ways:

### Option 1: As Validation Reference

Compare assembled hourly totals against 15-minute aggregated totals:

```bash
# Aggregate 15-min to hourly
nrgbnc aggregate \
  --csv data/swissgrid_15min_total.csv \
  --from-frequency 15min \
  --to-frequency 1h \
  --output data/swissgrid_hourly_total.csv

# Validate assembled series
nrgbnc validate total \
  --assembled-csv output/assembled_total_2016_2026.csv \
  --reference-csv data/swissgrid_hourly_total.csv \
  --start 2016-01-01 \
  --end 2026-12-31
```

### Option 2: As Additional Indicator

Use as a constraint in temporal disaggregation:

```python
# In benchmarking, add total production as additional indicator
# This helps preserve the overall temporal pattern
nrgbnc benchmark river \
  --high-frequency-csv data/entsoe_hourly.csv \
  --low-frequency-csv data/sfoe_daily.csv \
  --additional-indicator data/swissgrid_hourly_total.csv \
  --start 2016-01-01 \
  --end 2024-12-31
```

### Option 3: For Sub-Hourly Disaggregation

Disaggregate hourly to 15-minute using the total production pattern:

```bash
# First create hourly series
nrgbnc benchmark river --start 2024-01-01 --end 2024-12-31

# Then disaggregate to 15-min using total production pattern
nrgbnc disaggregate \
  --hourly-csv output/river_hourly_benchmarked_2024.csv \
  --pattern-csv data/swissgrid_15min_total.csv \
  --output output/river_15min_2024.csv
```

### Option 4: For Quality Checks

Check if sum of type-specific series matches total production:

```bash
# Assemble all types
nrgbnc assemble total --config config/all_types.yaml

# Compare with SwissGrid total
nrgbnc compare \
  --csv-a output/assembled_total.csv \
  --csv-b data/swissgrid_hourly_total.csv \
  --metric rmse \
  --metric bias
```

---

## Validation Workflow

### 1. Check Daily Balance

Verify that hourly sums match daily targets:

```bash
nrgbnc validate river \
  --csv-to-validate output/river_hourly_assembled.csv \
  --kind-of-csv benchmarked \
  --low-frequency-csv data/sfoe_daily.csv \
  --start 2016-01-01 \
  --end 2026-12-31
```

### 2. Compare Methods

Compare different methods for the same period:

```bash
nrgbnc compare \
  --csv-a output/river_scaled.csv \
  --csv-b output/river_benchmarked.csv \
  --metric rmse \
  --metric bias \
  --metric correlation
```

### 3. Plausibility Checks

Check for unrealistic values:

```bash
nrgbnc plausibility river \
  --csv output/river_hourly_assembled.csv \
  --start 2016-01-01 \
  --end 2026-12-31
```

### 4. Visual Inspection

Plot results for manual review:

```bash
# Before vs after
nrgbnc plot before-vs-after river \
  --csv output/river_hourly_assembled.csv \
  --start 2024-01-01 \
  --end 2024-12-31

# Original vs target
nrgbnc plot original-vs-target river \
  --high-frequency-csv data/entsoe_hourly.csv \
  --low-frequency-csv data/sfoe_daily.csv \
  --start 2024-01-01 \
  --end 2024-12-31
```

---

## Best Practices

### 1. Document Method Selection

Always document why you chose a specific method for each period:

```yaml
# config/river_assembly.yaml
metadata:
  description: "River hydro hourly series 2016-2026"
  methods:
    - period: "2016-2024"
      method: "benchmarking"
      reason: "ENTSO-E data incomplete (8-27x underreporting)"
    - period: "2025-2026"
      method: "advanced_scaling"
      reason: "ENTSO-E data nearly complete (1.1x ratio)"
```

### 2. Validate at Multiple Levels

- **Daily**: Sum of hourly = daily target
- **Monthly**: Aggregated patterns make sense
- **Annual**: Total generation matches official statistics
- **Cross-check**: Sum of types ≈ total production

### 3. Handle Edge Cases

- **Missing days**: Interpolate or use original values
- **Extreme factors**: Skip scaling, use benchmarking
- **Negative values**: Clip to zero or minimum
- **Zeros**: Preserve if meaningful (e.g., solar at night)

### 4. Version Control Results

Keep track of different versions:

```
output/
├── v1_simple_scaling/
├── v2_benchmarking/
├── v3_adaptive_assembly/
└── final/
```

### 5. Reproducibility

Save all parameters and configurations:

```bash
# Save command history
nrgbnc benchmark river ... > logs/benchmark_river_2024.log

# Save configuration
cp config/river_assembly.yaml output/final/config_used.yaml

# Save metadata
echo "Generated: $(date)" > output/final/metadata.txt
echo "Method: Adaptive assembly" >> output/final/metadata.txt
```

---

## Future Enhancements

### 1. Automatic Method Selection

Implement automatic selection based on data quality metrics:

```python
def select_best_method(data_quality_score):
    if score < 0.3:  # Very poor
        return "benchmarking"
    elif score < 0.7:  # Poor
        return "advanced_scaling"
    else:  # Good
        return "simple_scaling"
```

### 2. Multi-Indicator Disaggregation

Use multiple indicators simultaneously:

```python
nrgbnc benchmark river \
  --indicators entsoe_hourly.csv swissgrid_15min_total.csv \
  --weights 0.7 0.3 \
  --target sfoe_daily.csv
```

### 3. Ensemble Methods

Combine multiple methods with weights:

```python
nrgbnc ensemble river \
  --methods benchmarking scaling kalman \
  --weights 0.5 0.3 0.2 \
  --start 2016-01-01 \
  --end 2026-12-31
```

### 4. Machine Learning Approaches

Train models to learn optimal disaggregation:

```python
nrgbnc ml-disaggregate river \
  --train-period 2020-2024 \
  --test-period 2025-2026 \
  --features entsoe_hourly swissgrid_15min weather
```

---

## References

### Temporal Disaggregation Literature

- Chow, G. C., & Lin, A. L. (1971). "Best linear unbiased interpolation, distribution, and extrapolation of time series by related series"
- Denton, F. T. (1971). "Adjustment of monthly or quarterly series to annual totals: an approach based on quadratic minimization"
- Fernández, R. B. (1981). "A methodological note on the estimation of time series"

### Related Tools

- **tempdisagg** (R/Python): Temporal disaggregation methods
- **statsmodels**: State-space models and Kalman filtering
- **pandas**: Time series manipulation

---

## See Also

- [ENTSO-E Data Quality Issues](entsoe-data-quality-issues.md) - Understanding the data problem
- [Scaling Validation Guide](scaling-validation-guide.md) - Using validation features
- [Bias Comparison Guide](bias-comparison-guide.md) - Understanding metrics
- [AGENTS.md](../AGENTS.md) - Project overview and conventions
