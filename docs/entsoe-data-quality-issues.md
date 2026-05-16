# ENTSO-E Data Quality Issues for Swiss Hydro Run-of-river

## Critical Finding: Systematic Underreporting (2016-2024)

### Summary

ENTSO-E "Hydro Run-of-river and poundage" data for Switzerland is **systematically incomplete** from 2016-2024, reporting only a fraction of actual generation compared to official SFOE data. The data quality improves dramatically starting in 2025.

### Evidence

**Ratio Analysis (SFOE / ENTSO-E daily sums):**

| Year | Median Ratio | Range | Data Quality |
|------|--------------|-------|--------------|
| 2016 | 27.2x | 11-∞x | Very Poor (incomplete) |
| 2017 | 23.1x | 10-57x | Very Poor |
| 2018 | 10.8x | 7-43x | Poor |
| 2019 | 9.1x | 5-17x | Poor |
| 2020 | 8.3x | 6-14x | Poor |
| 2021 | 7.3x | 4-16x | Poor |
| 2022 | 8.5x | 5-19x | Poor |
| 2023 | 8.0x | 6-18x | Poor |
| 2024 | 8.3x | 6-14x | Poor |
| **2025** | **1.1x** | **1.0-10x** | **Good** ✅ |
| **2026** | **1.1x** | **0.9-1.4x** | **Excellent** ✅ |

**Overall median: 9.2x underreporting**

### Example: 2016-01-01

```
ENTSO-E Hydro Run-of-river: 0.744 GWh/day (24 hours × ~0.031 GW)
SFOE Flusskraft: 18.20 GWh/day
Ratio: 24.5x difference
```

### Root Cause

The ENTSO-E Transparency Platform had **incomplete reporting** of Swiss run-of-river hydro plants from 2016-2024. Possible reasons:

1. **Partial plant coverage**: Only large plants reported to ENTSO-E
2. **Reporting obligations**: Smaller plants not required to report
3. **Data aggregation issues**: Some plants excluded from aggregation
4. **Gradual improvement**: Coverage improved year-over-year (27x → 8x → 1x)

Starting in 2025, ENTSO-E data becomes nearly complete (ratio ~1.1x), suggesting improved reporting requirements or data collection.

---

## Impact on Scaling Operations

### Why This Causes Extreme Scaling Factors

When using simple or advanced scaling:

```python
scaling_factor = daily_target / daily_sum_of_hourly
```

With incomplete ENTSO-E data:
- `daily_sum_of_hourly` = 0.744 GWh (incomplete)
- `daily_target` = 18.20 GWh (complete, official)
- `scaling_factor` = 24.5x ⚠️

This creates **artificially high scaling factors** that distort the temporal patterns.

### Affected Commands

All scaling operations for `river` variable are affected:

```bash
# Simple scaling - affected 2016-2024
nrgbnc scale river ...

# Advanced scaling - affected 2016-2024  
nrgbnc scale advanced river ...
```

---

## Recommended Solutions

### Solution 1: Use Higher min_daily_sum Threshold (Quick Fix)

Skip scaling for days with unreliable data:

```bash
nrgbnc scale advanced river \
  --high-frequency-csv data/entsoe_hourly.csv \
  --low-frequency-csv data/sfoe_daily.csv \
  --start 2016-01-01 \
  --end 2024-12-31 \
  --min-daily-sum 2.0  # Skip days with sum < 2.0 GWh
```

**Pros:**
- Simple to implement
- Prevents extreme factors
- Keeps original values for unreliable days

**Cons:**
- Loses temporal adjustment for many days
- Output is mix of scaled and unscaled values

### Solution 2: Use Benchmarking Instead (Recommended)

Benchmarking (Chow-Lin) is more robust to systematic bias:

```bash
nrgbnc benchmark river \
  --high-frequency-csv data/entsoe_hourly.csv \
  --low-frequency-csv data/sfoe_daily.csv \
  --start 2016-01-01 \
  --end 2024-12-31
```

**Pros:**
- Handles systematic bias better
- Preserves temporal patterns
- Statistical method designed for this problem

**Cons:**
- Slower than scaling
- More complex algorithm

### Solution 3: Apply Correction Factor (Advanced)

Pre-scale ENTSO-E data by the known systematic bias before scaling:

```python
# For 2016-2024, multiply ENTSO-E values by median correction factor
correction_factors = {
    2016: 27.2,
    2017: 23.1,
    2018: 10.8,
    2019: 9.1,
    2020: 8.3,
    2021: 7.3,
    2022: 8.5,
    2023: 8.0,
    2024: 8.3,
}

# Then apply scaling with corrected values
```

**Pros:**
- Corrects systematic bias
- Allows normal scaling thresholds
- More accurate temporal patterns

**Cons:**
- Requires custom preprocessing
- Assumes constant correction factor within year

### Solution 4: Use Only 2025+ Data (Simplest)

If historical data is not critical, use only the reliable period:

```bash
nrgbnc scale river \
  --high-frequency-csv data/entsoe_hourly.csv \
  --low-frequency-csv data/sfoe_daily.csv \
  --start 2025-01-01 \
  --end 2026-12-31
```

**Pros:**
- Clean, reliable data
- No extreme factors
- Simple workflow

**Cons:**
- Limited historical coverage
- Not suitable if 2016-2024 data is needed

---

## Validation Commands

### Check Data Quality for Specific Period

```bash
# Compare ENTSO-E vs SFOE for a specific year
nrgbnc compare river \
  --csv-a data/entsoe_hourly.csv \
  --csv-b data/sfoe_daily.csv \
  --start 2020-01-01 \
  --end 2020-12-31
```

### Visualize the Systematic Bias

```bash
# Plot original vs target to see the gap
nrgbnc plot original-vs-target river \
  --high-frequency-csv data/entsoe_hourly.csv \
  --low-frequency-csv data/sfoe_daily.csv \
  --start 2016-01-01 \
  --end 2026-12-31
```

---

## Best Practices

### For 2016-2024 Data

1. **Use benchmarking** instead of scaling when possible
2. **If using scaling**, set `--min-daily-sum 2.0` or higher
3. **Document** that results are based on incomplete ENTSO-E data
4. **Consider** applying correction factors for better accuracy

### For 2025+ Data

1. **Standard scaling** works well (ratio ~1.1x)
2. **Default thresholds** are appropriate
3. **No special handling** needed

### For Mixed Periods

```bash
# Process 2016-2024 with benchmarking
nrgbnc benchmark river \
  --start 2016-01-01 \
  --end 2024-12-31 \
  --output-dir output/historical

# Process 2025+ with scaling
nrgbnc scale river \
  --start 2025-01-01 \
  --end 2026-12-31 \
  --output-dir output/recent

# Combine results
nrgbnc assemble river \
  --csv-files output/historical/river_*.csv output/recent/river_*.csv \
  --output output/river_combined.csv
```

---

## Technical Notes

### Why Benchmarking Works Better

Temporal disaggregation methods like Chow-Lin:
- Model the **relationship** between high and low frequency series
- Handle **systematic bias** through regression
- Preserve **temporal patterns** while matching targets
- More robust to **data quality issues**

### Why Simple Scaling Fails

Simple scaling assumes:
- High-frequency data is **complete** (just needs adjustment)
- Ratio between series is **relatively constant**
- Only **minor corrections** needed

These assumptions break down with 9-27x systematic underreporting.

---

## See Also

- [Scaling Validation Guide](scaling-validation-guide.md) - Using min_daily_sum and warn_threshold
- [Bias Comparison Guide](bias-comparison-guide.md) - Understanding bias metrics
- [AGENTS.md](../AGENTS.md) - Project overview and conventions
