"""
Unified comparison interface for comparing any two series.
"""

from pathlib import Path
from typing import Literal
import pandas as pd
from pandas import Timestamp

from energybench.core.metrics import compare_series
from energybench.core.validation import KindOfCSV
from energybench.helpers import sum_columns
from energybench.io.reading import read_csv
from energybench.io.writing import save_dataframe
from energybench.print.metrics import print_metrics
from energybench.variables import get_variable_config


SeriesType = Literal["indicator", "adjusted", "target"]


def compare_series_unified(
    series1: SeriesType,
    series2: SeriesType,
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
    indicator_time_column: str = "DateTime",
    target_time_column: str = "Date",
    adjusted_time_column: str = "DateTime",
) -> pd.DataFrame:
    """
    Compare any two series: indicator, adjusted, or target.

    Valid combinations:
    - indicator vs target: Shows why adjustment is needed (bias, differences)
    - indicator vs adjusted: Shows what changed during adjustment
    - adjusted vs target: Validates adjustment worked correctly

    Parameters
    ----------
    series1 : {"indicator", "adjusted", "target"}
        First series to compare.
    series2 : {"indicator", "adjusted", "target"}
        Second series to compare.
    variable : str
        Energy type (e.g., "river", "nuclear", "solar").
    start : pd.Timestamp
        Start timestamp for comparison period.
    end : pd.Timestamp
        End timestamp for comparison period.
    indicator_csv : Path, optional
        Path to indicator CSV file. Required if series1 or series2 is "indicator".
    adjusted_csv : Path, optional
        Path to adjusted CSV file. Required if series1 or series2 is "adjusted".
    target_csv : Path, optional
        Path to target CSV file. Required if series1 or series2 is "target".
    kind_of_adjusted : KindOfCSV, default=KindOfCSV.benchmarked
        Type of adjusted series to use (benchmarked, scaled, or scaled-per-day).
    output_csv : Path, optional
        Path to save comparison metrics CSV. If None, metrics are not saved.
    indicator_time_column : str, default="DateTime"
        Name of datetime column in indicator CSV.
    target_time_column : str, default="Date"
        Name of datetime column in target CSV.
    adjusted_time_column : str, default="DateTime"
        Name of datetime column in adjusted CSV.

    Returns
    -------
    pd.DataFrame
        DataFrame with comparison metrics including correlation, error metrics,
        and summary statistics.

    Raises
    ------
    ValueError
        If series1 equals series2, or if required CSV files are not provided.

    Examples
    --------
    Compare indicator vs target to show why adjustment is needed:

    >>> metrics = compare_series_unified(
    ...     series1="indicator",
    ...     series2="target",
    ...     variable="river",
    ...     indicator_csv=Path("data/entsoe.csv"),
    ...     target_csv=Path("data/sfoe.csv"),
    ...     start=pd.Timestamp("2024-01-01"),
    ...     end=pd.Timestamp("2024-12-31"),
    ... )

    Compare indicator vs adjusted to show what changed:

    >>> metrics = compare_series_unified(
    ...     series1="indicator",
    ...     series2="adjusted",
    ...     variable="river",
    ...     indicator_csv=Path("data/entsoe.csv"),
    ...     adjusted_csv=Path("output/river_benchmarked.csv"),
    ...     start=pd.Timestamp("2024-01-01"),
    ...     end=pd.Timestamp("2024-12-31"),
    ... )

    Compare adjusted vs target to validate adjustment:

    >>> metrics = compare_series_unified(
    ...     series1="adjusted",
    ...     series2="target",
    ...     variable="river",
    ...     adjusted_csv=Path("output/river_benchmarked.csv"),
    ...     target_csv=Path("data/sfoe.csv"),
    ...     start=pd.Timestamp("2024-01-01"),
    ...     end=pd.Timestamp("2024-12-31"),
    ... )
    """
    # Validate inputs
    if series1 == series2:
        raise ValueError(f"Cannot compare series with itself: {series1}")
    
    # Check required files are provided
    required_files = {
        "indicator": ("indicator_csv", indicator_csv),
        "adjusted": ("adjusted_csv", adjusted_csv),
        "target": ("target_csv", target_csv),
    }
    
    for series_name in [series1, series2]:
        param_name, param_value = required_files[series_name]
        if param_value is None:
            raise ValueError(
                f"--{param_name.replace('_', '-')} is required when comparing '{series_name}'"
            )
    
    # Get variable configuration
    cfg = get_variable_config(variable)
    
    # Load series based on type
    def load_series(series_type: str) -> pd.Series:
        if series_type == "indicator":
            df = read_csv(
                indicator_csv,
                start=start,
                end=end,
                time_column=indicator_time_column,
            )
            return sum_columns(
                df,
                cfg["indicator_types_present"],
                "indicator",
            )
        
        elif series_type == "adjusted":
            df = pd.read_csv(
                adjusted_csv,
                parse_dates=[adjusted_time_column],
            )
            df = df.set_index(adjusted_time_column).loc[start:end]
            
            # Get the appropriate column based on kind_of_adjusted
            col_map = {
                KindOfCSV.benchmarked: cfg["benchmarked_column"],
                KindOfCSV.scaled: cfg["scaled_column"],
                KindOfCSV.scaled_per_day: cfg["scaled_advanced_column"],
            }
            col = col_map[kind_of_adjusted]
            return df[col].rename("adjusted")
        
        elif series_type == "target":
            df = read_csv(
                target_csv,
                start=start.normalize(),
                end=end.normalize(),
                time_column=target_time_column,
            )
            return sum_columns(
                df,
                cfg["target_types_present"],
                "target",
            )
    
    # Load both series
    print(f"📖 Loading {series1} series...")
    s1 = load_series(series1)
    
    print(f"📖 Loading {series2} series...")
    s2 = load_series(series2)
    
    # Aggregate to daily for comparison
    print(f"📊 Aggregating to daily frequency...")
    s1_daily = s1.resample("D").sum()
    s2_daily = s2.resample("D").sum()
    
    # Calculate metrics
    print(f"🔬 Calculating comparison metrics...")
    metrics = compare_series(s1_daily, s2_daily)
    
    # Calculate bias percentage
    if metrics.mean_b not in (0, None):
        bias_pct = (metrics.mean_a / metrics.mean_b - 1.0) * 100.0
    else:
        bias_pct = float("nan")
    
    # Build output row
    row = {
        "comparison": f"{series1}_vs_{series2}",
        "variable": variable,
        "start": start,
        "end": end,
        "n_days": len(s1_daily),
        **metrics.to_dict(),
        "bias_pct": bias_pct,
    }
    
    # Print results
    print(f"\n{'='*70}")
    print(f"📊 Comparison: {series1.upper()} vs {series2.upper()}")
    print(f"{'='*70}")
    print(f"Variable: {cfg['label']}")
    print(f"Period: {start.date()} to {end.date()}")
    print(f"Days: {len(s1_daily)}")
    print(f"\nSummary Statistics:")
    print(f"  {series1.capitalize()} - Mean: {metrics.mean_a:.4f} GWh, Std: {metrics.std_a:.4f} GWh, Sum: {metrics.sum_a:.2f} GWh")
    print(f"  {series2.capitalize()} - Mean: {metrics.mean_b:.4f} GWh, Std: {metrics.std_b:.4f} GWh, Sum: {metrics.sum_b:.2f} GWh")
    print(f"\nComparison Metrics:")
    print(f"  Pearson correlation: {metrics.pearson:.4f}")
    print(f"  Spearman correlation: {metrics.spearman:.4f}")
    print(f"  Cosine similarity: {metrics.cosine:.4f}")
    print(f"\nError Metrics:")
    print(f"  Mean Bias Error (MBE): {metrics.mbe:+.4f} GWh")
    print(f"  Mean Absolute Error (MAE): {metrics.mae:.4f} GWh")
    print(f"  Root Mean Square Error (RMSE): {metrics.rmse:.4f} GWh")
    print(f"  Normalized RMSE: {metrics.nrmse_mean:.2f}%")
    print(f"  SMAPE: {metrics.smape:.2f}%")
    print(f"  Bias: {bias_pct:+.2f}%")
    
    if metrics.best_lag is not None:
        print(f"\nTemporal Analysis:")
        print(f"  Best lag: {metrics.best_lag} days")
        print(f"  Correlation at best lag: {metrics.best_lag_corr:.4f}")
    
    print(f"{'='*70}\n")
    
    # Save metrics if requested
    if output_csv:
        df = pd.DataFrame([row])
        
        # Reorder columns for better readability
        preferred_order = [
            "comparison",
            "variable",
            "start",
            "end",
            "n_days",
            "pearson",
            "spearman",
            "cosine",
            "mbe",
            "mae",
            "rmse",
            "nrmse_mean",
            "smape",
            "bias_pct",
            "mean_a",
            "mean_b",
            "std_a",
            "std_b",
            "sum_a",
            "sum_b",
            "best_lag",
            "best_lag_corr",
        ]
        cols = [c for c in preferred_order if c in df.columns] + [
            c for c in df.columns if c not in preferred_order
        ]
        df = df[cols]
        
        save_dataframe(
            df,
            output_csv,
            output_csv.parent if output_csv.is_absolute() else Path("output"),
            variable,
            index=False,
        )
        print(f"💾 Metrics saved to: {output_csv}")
    
    return pd.DataFrame([row])
