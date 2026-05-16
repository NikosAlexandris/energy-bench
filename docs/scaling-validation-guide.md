# Scaling Validation Guide

## Understanding Extreme Scaling Factors

### What Causes Extreme Scaling?

Extreme scaling factors occur when the **hourly sum for a day is very small** but the **daily target is normal**. This creates a huge multiplication factor.

**Example:**
```
Hourly values: [0.001, 0.001, 0.001, ...] → sum = 0.024 GWh
Daily target: 50 GWh
Scaling factor: 50 / 0.024 = 2083x 🚨
Result: Scaled values become [2.08, 2.08, 2.08, ...] → huge spikes!
```

### Common Causes

1. **Data quality issues**: Missing or incomplete hourly data
2. **Timezone mismatches**: Data recorded in different timezones
3. **Partial days**: Incomplete data at the start/end of time ranges
4. **Sensor failures**: Temporary outages in data collection
5. **Data processing errors**: Issues in upstream data pipelines

---

## Built-in Validation Features

Both `scale` and `scale advanced` commands now include automatic validation:

### Default Parameters

```bash
--warn-threshold 10.0      # Warn if scaling factor exceeds 10x
--min-daily-sum 0.01       # Skip scaling if daily sum < 0.01 GWh
```

### Example Output

```bash
nrgbnc scale river \
  --high-frequency-csv data/entsoe_hourly.csv \
  --low-frequency-csv data/sfoe_daily.csv \
  --start 2024-01-01 \
  --end 2024-01-31
```

**Console output:**
```
⚠️  Warning: 9 days have extreme scaling factors (>10.0x):
   2024-01-16: factor=10.4x (daily_sum=3.7787 GWh, target=39.40 GWh)
   2024-01-17: factor=10.5x (daily_sum=4.1426 GWh, target=43.60 GWh)
   2024-01-18: factor=13.4x (daily_sum=3.9275 GWh, target=52.60 GWh)
   2024-01-19: factor=10.5x (daily_sum=4.7781 GWh, target=50.20 GWh)
   2024-01-23: factor=12.5x (daily_sum=3.5187 GWh, target=43.90 GWh)
   ... and 4 more days
💾 Output written to output/river_hourly_scaled_2024.csv
```

---

## Customizing Validation Thresholds

### Adjust Warning Threshold

```bash
# More sensitive (warn at 5x)
nrgbnc scale river \
  --high-frequency-csv data/entsoe_hourly.csv \
  --low-frequency-csv data/sfoe_daily.csv \
  --start 2024-01-01 \
  --end 2024-12-31 \
  --warn-threshold 5.0

# Less sensitive (warn at 20x)
nrgbnc scale river \
  --high-frequency-csv data/entsoe_hourly.csv \
  --low-frequency-csv data/sfoe_daily.csv \
  --start 2024-01-01 \
  --end 2024-12-31 \
  --warn-threshold 20.0
```

### Adjust Minimum Daily Sum

```bash
# Stricter (skip scaling if sum < 0.1 GWh)
nrgbnc scale river \
  --high-frequency-csv data/entsoe_hourly.csv \
  --low-frequency-csv data/sfoe_daily.csv \
  --start 2024-01-01 \
  --end 2024-12-31 \
  --min-daily-sum 0.1

# More lenient (skip only if sum < 0.001 GWh)
nrgbnc scale river \
  --high-frequency-csv data/entsoe_hourly.csv \
  --low-frequency-csv data/sfoe_daily.csv \
  --start 2024-01-01 \
  --end 2024-12-31 \
  --min-daily-sum 0.001
```

---

## Advanced Scaling Protection

The `scale advanced` command includes additional protection:

### Automatic Skip for Very Small Sums

When `min_daily_sum` threshold is triggered, the advanced method **skips scaling** for those days and keeps original values:

```bash
nrgbnc scale advanced river \
  --high-frequency-csv data/entsoe_hourly.csv \
  --low-frequency-csv data/sfoe_daily.csv \
  --start 2024-01-01 \
  --end 2024-12-31 \
  --min-daily-sum 0.1
```

**Console output:**
```
⚠️  Warning: 3 days have very small hourly sums (<0.1 GWh):
   These days were NOT scaled to avoid extreme values.
   2024-01-05: sum=0.0234 GWh (target=45.20 GWh)
   2024-01-12: sum=0.0156 GWh (target=38.90 GWh)
   2024-01-28: sum=0.0891 GWh (target=42.30 GWh)
   Consider checking data quality or adjusting min_daily_sum parameter.
```

### Combined with Other Constraints

```bash
nrgbnc scale advanced river \
  --high-frequency-csv data/entsoe_hourly.csv \
  --low-frequency-csv data/sfoe_daily.csv \
  --start 2024-01-01 \
  --end 2024-12-31 \
  --min-value 0.0 \
  --preserve-zeros true \
  --warn-threshold 10.0 \
  --min-daily-sum 0.05
```

---

## Investigating Extreme Factors

### Step 1: Identify Problem Days

Run scaling with default validation to see warnings:

```bash
nrgbnc scale river \
  --high-frequency-csv data/entsoe_hourly.csv \
  --low-frequency-csv data/sfoe_daily.csv \
  --start 2024-01-01 \
  --end 2024-12-31
```

### Step 2: Examine Specific Days

Use the dates from warnings to investigate:

```bash
# Check hourly data for a specific day
grep "2024-01-16" data/entsoe_hourly.csv | head -24

# Check daily target
grep "2024-01-16" data/sfoe_daily.csv
```

### Step 3: Decide on Action

**Option A: Accept the scaling** (if data is correct but just low)
```bash
# Use higher warn-threshold to suppress warnings
nrgbnc scale river ... --warn-threshold 20.0
```

**Option B: Skip problematic days** (if data is unreliable)
```bash
# Use higher min-daily-sum to skip scaling
nrgbnc scale advanced river ... --min-daily-sum 1.0
```

**Option C: Fix source data** (if data is clearly wrong)
- Correct the ENTSO-E hourly data
- Re-run scaling with corrected data

---

## Best Practices

### 1. Always Review Warnings

Don't ignore validation warnings - they indicate potential data quality issues that could affect your analysis.

### 2. Start with Default Thresholds

The defaults (`warn-threshold=10.0`, `min-daily-sum=0.01`) are reasonable for most cases. Only adjust if you have specific requirements.

### 3. Use Advanced Scaling for Critical Data

When data quality is uncertain, use `scale advanced` with protection:

```bash
nrgbnc scale advanced river \
  --high-frequency-csv data/entsoe_hourly.csv \
  --low-frequency-csv data/sfoe_daily.csv \
  --start 2024-01-01 \
  --end 2024-12-31 \
  --min-daily-sum 0.1  # Skip days with very small sums
```

### 4. Document Your Choices

When you adjust thresholds, document why:

```bash
# Using higher threshold because river data is naturally variable
# and 10x factors are acceptable for this energy type
nrgbnc scale river ... --warn-threshold 15.0
```

### 5. Validate Results

After scaling, always validate the output:

```bash
nrgbnc validate river \
  --csv-to-validate output/river_hourly_scaled_2024.csv \
  --kind-of-csv scaled \
  --high-frequency-csv data/entsoe_hourly.csv \
  --low-frequency-csv data/sfoe_daily.csv \
  --start 2024-01-01 \
  --end 2024-12-31
```

---

## Troubleshooting

### Too Many Warnings

**Problem**: Getting warnings for many days

**Solutions**:
1. Check data quality in source files
2. Increase `warn-threshold` if factors are acceptable
3. Use `scale advanced` with higher `min-daily-sum`

### Spikes at End of Time Range

**Problem**: Extreme values at the end of the scaled series

**Cause**: Incomplete data at the end of the time range

**Solutions**:
1. Adjust `end` date to exclude incomplete days
2. Use `scale advanced` with `min-daily-sum` protection
3. Fix source data to include complete days

### Inconsistent Results

**Problem**: Different scaling factors for similar days

**Cause**: Variable data quality in hourly series

**Solutions**:
1. Use `scale advanced` for more consistent results
2. Apply data cleaning before scaling
3. Use benchmarking instead of scaling for better temporal consistency

---

## Technical Details

### Simple Scaling Algorithm

```python
factor = daily_target / daily_sum_of_hourly
scaled_hourly = hourly * factor

# With validation:
if daily_sum < min_daily_sum:
    # Keep original values
    scaled_hourly = hourly
elif abs(factor) > warn_threshold:
    # Warn but still scale
    print(f"Warning: extreme factor {factor}x")
```

### Advanced Scaling Algorithm

```python
for each day:
    if daily_sum < min_daily_sum:
        # Skip scaling, keep original
        continue
    
    factor = daily_target / daily_sum
    
    if abs(factor) > warn_threshold:
        # Warn but still scale
        print(f"Warning: extreme factor {factor}x")
    
    # Apply constraints
    scaled = hourly * factor
    scaled = scaled.clip(min=min_value)
    
    if preserve_zeros:
        # Keep original zeros
        scaled[hourly == 0] = 0
        # Redistribute remainder
```

---

## See Also

- [Bias Comparison Guide](bias-comparison-guide.md) - Understanding bias metrics
- [AGENTS.md](../AGENTS.md) - Project overview and conventions
- [README.md](../README.md) - Getting started guide
