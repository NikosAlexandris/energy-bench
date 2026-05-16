# Automated Bias Detection and Subperiod Analysis Guide

## Overview

The automated bias detection system analyzes time series data to identify patterns, detect changepoints, cluster similar periods, and recommend optimal adjustment strategies for different subperiods. This eliminates the need for manual trial-and-error when determining which adjustment method works best for your data.

## Key Features

### 1. **Rolling Window Analysis**
- Analyzes bias patterns using sliding time windows
- Configurable window size (e.g., 30 days) and step size (e.g., 7 days)
- Tracks bias percentage, MAE, RMSE, and correlation over time

### 2. **Changepoint Detection**
- Automatically identifies when bias characteristics change significantly
- Supports multiple detection methods:
  - **Threshold-based**: Simple detection based on absolute change
  - **Binary Segmentation**: Recursive splitting to find optimal breakpoints
- Helps identify periods that should be treated differently

### 3. **Period Clustering**
- Groups time periods with similar bias characteristics
- Uses K-means clustering on multiple features (bias, MAE, RMSE, correlation)
- Identifies distinct patterns in your data

### 4. **Method Recommendation Engine**
- Automatically recommends the best adjustment method for each subperiod:
  - **Scaling**: For low bias (<5%) with high correlation (>0.9)
  - **Benchmarking**: For high bias (>20%) or low correlation (<0.7)
  - **Advanced Scaling**: For moderate bias with good correlation
  - **Kalman**: For periods with high variability
- Provides confidence scores and expected improvements

### 5. **Comprehensive Visualizations**
- Overview plot showing bias, errors, correlation, and recommendations over time
- Cluster characteristics comparison
- Timeline view of recommendations with confidence levels

## Installation

The bias detection module is included in the energy-bench package. Ensure you have the required dependencies:

```bash
# Install with all dependencies
uv sync

# Or with pip
pip install -e .
```

Required packages:
- `pandas`
- `numpy`
- `scipy`
- `scikit-learn`
- `matplotlib`

## Usage

### Basic Command

```bash
nrgbnc analyze bias-patterns <variable> \
  --high-frequency-csv <path-to-entsoe-data> \
  --low-frequency-csv <path-to-sfoe-data> \
  --start <start-date> \
  --end <end-date> \
  --output-csv <output-recommendations.csv> \
  --output-summary <output-summary.txt> \
  --output-plot <output-plot.png>
```

### Complete Example

```bash
nrgbnc analyze bias-patterns river \
  --high-frequency-csv data/entsoe_hourly.csv \
  --low-frequency-csv data/sfoe_daily.csv \
  --start 2018-01-01 \
  --end 2024-12-31 \
  --output-csv output/river_bias_analysis.csv \
  --output-summary output/river_bias_summary.txt \
  --output-plot output/river_bias_overview.png \
  --output-clusters-plot output/river_clusters.png \
  --output-timeline-plot output/river_timeline.png \
  --window-size 30D \
  --step-size 7D \
  --n-clusters 3 \
  --changepoint-method threshold \
  --changepoint-threshold 5.0
```

## Parameters

### Required Parameters

- `variable`: Energy type to analyze (e.g., 'river', 'solar', 'nuclear')
- `--high-frequency-csv`: Path to ENTSO-E hourly data
- `--low-frequency-csv`: Path to SFOE daily data
- `--start`: Start date (YYYY-MM-DD)
- `--end`: End date (YYYY-MM-DD)

### Optional Parameters

#### Output Options
- `--output-csv`: Path for recommendations CSV
- `--output-summary`: Path for text summary report
- `--output-plot`: Path for main visualization
- `--output-clusters-plot`: Path for cluster characteristics plot
- `--output-timeline-plot`: Path for recommendation timeline plot

#### Analysis Configuration
- `--window-size`: Rolling window size (default: `30D`)
  - Examples: `7D`, `30D`, `60D`, `90D`
- `--step-size`: Step between windows (default: `7D`)
  - Examples: `1D`, `7D`, `14D`
- `--n-clusters`: Number of clusters (default: `3`)
  - Typical range: 2-5
- `--changepoint-method`: Detection method (default: `threshold`)
  - Options: `threshold`, `binary_segmentation`
- `--changepoint-threshold`: Threshold for detection (default: `5.0`)
  - For bias percentage change

#### Data Column Names
- `--high-frequency-datetime-column`: DateTime column in ENTSO-E data (default: `DateTime`)
- `--low-frequency-date-column`: Date column in SFOE data (default: `Date`)

## Output Files

### 1. Recommendations CSV

Contains detailed recommendations for each subperiod:

| Column | Description |
|--------|-------------|
| `start` | Period start date |
| `end` | Period end date |
| `method` | Recommended adjustment method |
| `confidence` | Confidence score (0-1) |
| `reason` | Explanation for recommendation |
| `cluster_id` | Associated cluster ID (if applicable) |
| `expected_bias_reduction_pct` | Expected bias improvement |
| `expected_mae_reduction_pct` | Expected MAE improvement |
| `expected_rmse_reduction_pct` | Expected RMSE improvement |

### 2. Summary Report

Text file containing:
- Overall statistics (bias, MAE, RMSE)
- Number of changepoints detected
- Number of clusters identified
- Top recommendations with details
- Cluster characteristics
- Changepoint information

### 3. Visualizations

#### Overview Plot (4 panels)
1. **Bias % over time**: Shows bias trends with changepoints marked
2. **MAE and RMSE over time**: Error metrics evolution
3. **Correlation over time**: Pearson correlation trends
4. **Recommended methods**: Timeline of method recommendations

#### Cluster Characteristics Plot (4 panels)
1. **Cluster sizes**: Number of periods in each cluster
2. **Bias by cluster**: Mean bias percentage per cluster
3. **Error metrics**: MAE and RMSE comparison
4. **Correlation**: Mean correlation per cluster

#### Timeline Plot
- Horizontal bars showing recommendations over time
- Bar height represents confidence level
- Color-coded by method
- Includes confidence percentages

## Interpretation Guide

### Understanding Clusters

**What are clusters?**
Clusters are groups of **rolling window periods** that exhibit similar bias characteristics. Each "period" represents one analysis window (e.g., 30 days of data).

**Example**: With window_size=30D and step_size=7D analyzing one year:
- Creates ~50 overlapping windows (each analyzing 30 days)
- Each window is one "period" that gets assigned to a cluster
- Cluster 0 might have 32 periods (windows) with similar moderate bias
- Cluster 1 might have 4 periods with severe bias
- Cluster 2 might have 14 periods with minimal bias

**How to interpret the cluster plot:**

1. **Cluster Sizes (Panel 1)**: Number of rolling windows in each cluster
   - Large clusters = common bias pattern (e.g., 32 windows with -13% bias)
   - Small clusters = rare pattern (e.g., 4 windows with -17% bias)

2. **Bias by Cluster (Panel 2)**: Average bias for windows in each cluster
   - Negative = indicator underestimates target
   - Positive = indicator overestimates target
   - Helps identify if certain time periods consistently under/over-estimate

3. **Error Metrics (Panel 3)**: MAE and RMSE for each cluster
   - Higher values = larger absolute errors
   - Compare MAE vs RMSE: if RMSE >> MAE, there are outliers

4. **Correlation (Panel 4)**: How well indicator shape matches target shape
   - High correlation (>0.9) = good shape match, just needs scaling
   - Low correlation (<0.7) = shape mismatch, needs temporal disaggregation

**Practical interpretation:**
- **Cluster with low bias + high correlation** → Use simple scaling
- **Cluster with high bias or low correlation** → Use benchmarking
- **Multiple distinct clusters** → Different time periods need different methods
- **One dominant cluster** → Consistent bias pattern throughout

**Example from river 2025 analysis:**
```
Cluster 2 (14 periods): -0.30% bias, 0.99 correlation → scaling (90% confidence)
  Interpretation: 14 windows (~3-4 months) where data is nearly perfect
  
Cluster 0 (32 periods): -13.86% bias, 0.95 correlation → advanced_scaling (75% confidence)
  Interpretation: Most of the year has moderate underestimation but good shape
  
Cluster 1 (4 periods): -16.88% bias, 0.92 correlation → benchmarking (80% confidence)
  Interpretation: Brief period (~1 month) with severe underestimation
```

### Bias Percentage
- **< 5%**: Low bias - simple scaling may suffice
- **5-20%**: Moderate bias - consider advanced methods
- **> 20%**: High bias - temporal disaggregation recommended

### Correlation (Pearson r)
- **> 0.9**: Excellent - shape matches well
- **0.7-0.9**: Good - minor shape differences
- **< 0.7**: Poor - significant shape mismatch

### Confidence Scores
- **> 0.8**: High confidence - strong recommendation
- **0.6-0.8**: Moderate confidence - good recommendation
- **< 0.6**: Low confidence - consider alternatives

### Method Selection Logic

The system recommends methods based on these criteria:

| Condition | Recommended Method | Reason |
|-----------|-------------------|--------|
| Bias < 5% AND r > 0.9 | **Scaling** | Low bias, high correlation |
| Bias > 20% OR r < 0.7 | **Benchmarking** | High bias or shape mismatch |
| MAE > 0.8 × RMSE | **Advanced Scaling** | Moderate systematic error |
| Otherwise | **Kalman** | High variability |

## Workflow Examples

### Example 1: Quick Analysis

Analyze river data and get recommendations:

```bash
nrgbnc analyze bias-patterns river \
  --high-frequency-csv data/entsoe_hourly.csv \
  --low-frequency-csv data/sfoe_daily.csv \
  --start 2020-01-01 \
  --end 2024-12-31 \
  --output-csv output/river_recommendations.csv
```

### Example 2: Comprehensive Analysis with Visualizations

Full analysis with all outputs:

```bash
nrgbnc analyze bias-patterns solar \
  --high-frequency-csv data/entsoe_hourly.csv \
  --low-frequency-csv data/sfoe_daily.csv \
  --start 2015-01-01 \
  --end 2024-12-31 \
  --output-csv output/solar_recommendations.csv \
  --output-summary output/solar_summary.txt \
  --output-plot output/solar_overview.png \
  --output-clusters-plot output/solar_clusters.png \
  --output-timeline-plot output/solar_timeline.png \
  --window-size 60D \
  --step-size 14D \
  --n-clusters 4
```

### Example 3: Fine-Tuned Detection

Adjust sensitivity for changepoint detection:

```bash
nrgbnc analyze bias-patterns nuclear \
  --high-frequency-csv data/entsoe_hourly.csv \
  --low-frequency-csv data/sfoe_daily.csv \
  --start 2016-01-01 \
  --end 2025-12-31 \
  --output-csv output/nuclear_recommendations.csv \
  --changepoint-method binary_segmentation \
  --changepoint-threshold 3.0 \
  --window-size 45D \
  --step-size 10D
```

### Example 4: Analyze All Energy Types

Batch analysis for all variables:

```bash
for var in river solar nuclear storage water wind thermal; do
  echo "Analyzing $var..."
  nrgbnc analyze bias-patterns $var \
    --high-frequency-csv data/entsoe_hourly.csv \
    --low-frequency-csv data/sfoe_daily.csv \
    --start 2018-01-01 \
    --end 2024-12-31 \
    --output-csv output/${var}_recommendations.csv \
    --output-summary output/${var}_summary.txt \
    --output-plot output/${var}_overview.png
done
```

## Using the Recommendations

Once you have the recommendations, apply them to your data:

### Step 1: Review Recommendations

```bash
# View the summary
cat output/river_summary.txt

# Or load CSV in Python/pandas
import pandas as pd
recs = pd.read_csv('output/river_recommendations.csv')
print(recs)
```

### Step 2: Apply Recommended Methods

For each recommended period, use the appropriate command:

#### Scaling
```bash
nrgbnc scale river \
  --high-frequency-csv data/entsoe_hourly.csv \
  --low-frequency-csv data/sfoe_daily.csv \
  --start 2020-01-01 \
  --end 2020-12-31 \
  --output-csv output/river_scaled_2020.csv
```

#### Benchmarking
```bash
nrgbnc benchmark river \
  --high-frequency-csv data/entsoe_hourly.csv \
  --low-frequency-csv data/sfoe_daily.csv \
  --start 2021-01-01 \
  --end 2021-12-31 \
  --output-csv output/river_benchmarked_2021.csv
```

#### Advanced Scaling
```bash
nrgbnc scale river \
  --high-frequency-csv data/entsoe_hourly.csv \
  --low-frequency-csv data/sfoe_daily.csv \
  --start 2022-01-01 \
  --end 2022-12-31 \
  --output-csv output/river_advanced_2022.csv \
  --method advanced
```

### Step 3: Combine Results

After processing each subperiod, combine them:

```bash
nrgbnc assemble \
  --input-csvs output/river_scaled_2020.csv \
              output/river_benchmarked_2021.csv \
              output/river_advanced_2022.csv \
  --output-csv output/river_combined_2020_2022.csv
```

## Advanced Usage

### Python API

You can also use the bias detection system programmatically:

```python
import pandas as pd
from energybench.analyze.bias_detection import detect_bias_patterns
from energybench.analyze.visualize import plot_bias_detection_overview
from energybench.read import read_csv
from energybench.helpers import sum_columns
from energybench.variables import get_variable_config

# Load data
hf_df = read_csv('data/entsoe_hourly.csv', time_column='DateTime')
lf_df = read_csv('data/sfoe_daily.csv', time_column='Date')

# Get configuration
config = get_variable_config('river')

# Prepare series
indicator = sum_columns(hf_df, config['indicator_types_present'])
target = sum_columns(lf_df, config['target_types_present'])

# Run analysis
result = detect_bias_patterns(
    indicator=indicator,
    target=target,
    variable='river',
    window_size='30D',
    step_size='7D',
    n_clusters=3,
)

# Print summary
print(result.to_summary())

# Save recommendations
df = result.to_dataframe()
df.to_csv('output/recommendations.csv', index=False)

# Create visualizations
plot_bias_detection_overview(result, output_path='output/overview.png')
```

### Custom Analysis

Access individual components:

```python
from energybench.analyze.bias_detection import (
    rolling_bias_analysis,
    detect_changepoints,
    cluster_periods,
    recommend_adjustment_strategy,
)

# Rolling window analysis
windows = rolling_bias_analysis(
    indicator, target,
    window_size='30D',
    step_size='7D',
)

# Detect changepoints
changepoints = detect_changepoints(
    windows,
    method='threshold',
    threshold=5.0,
)

# Cluster periods
clusters = cluster_periods(windows, n_clusters=3)

# Generate recommendations
recommendations = recommend_adjustment_strategy(
    windows, changepoints, clusters
)
```

## Troubleshooting

### Issue: No changepoints detected

**Solution**: Lower the `--changepoint-threshold` or try `--changepoint-method binary_segmentation`

### Issue: Too many clusters

**Solution**: Reduce `--n-clusters` to 2 or 3

### Issue: Low confidence scores

**Possible causes**:
- Insufficient data in windows (increase `--window-size`)
- High variability in bias patterns
- Data quality issues

**Solution**: Review the visualizations to understand patterns better

### Issue: Recommendations don't match expectations

**Solution**: 
- Check the cluster characteristics plot
- Review individual window statistics
- Adjust clustering parameters
- Consider domain knowledge when interpreting results

## Best Practices

1. **Start with default parameters** and adjust based on results
2. **Use longer windows** (60D-90D) for stable patterns
3. **Use shorter windows** (14D-30D) for rapidly changing patterns
4. **Review visualizations** before applying recommendations
5. **Validate results** by comparing adjusted data to targets
6. **Document your choices** for reproducibility

## Integration with Existing Workflow

The bias detection system complements existing commands:

```bash
# 1. Detect patterns and get recommendations
nrgbnc analyze bias-patterns river \
  --high-frequency-csv data/entsoe_hourly.csv \
  --low-frequency-csv data/sfoe_daily.csv \
  --start 2020-01-01 \
  --end 2024-12-31 \
  --output-csv output/river_recs.csv

# 2. Apply recommended methods (based on recommendations)
nrgbnc scale river ... # for periods with scaling recommendation
nrgbnc benchmark river ... # for periods with benchmarking recommendation

# 3. Validate results
nrgbnc validate ... 

# 4. Compare before/after
nrgbnc compare ...

# 5. Visualize
nrgbnc plot ...
```

## References

- **Temporal Disaggregation**: See `docs/temporal-disaggregation-methodology.md`
- **Scaling Methods**: See `docs/scaling-validation-guide.md`
- **Bias Comparison**: See `docs/bias-comparison-guide.md`
- **Data Quality**: See `docs/entsoe-data-quality-issues.md`

## Support

For issues or questions:
1. Check the documentation in `docs/`
2. Review example outputs in `output/`
3. Examine the code in `src/energybench/analyze/`
4. Refer to AGENTS.md for development context
