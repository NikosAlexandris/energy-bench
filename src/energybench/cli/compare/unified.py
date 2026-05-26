"""
Unified comparison interface for comparing any two series.
"""

from pathlib import Path
from typing import Literal
import pandas as pd
from pandas import Timestamp

from energybench.core.metrics import compare_series
from energybench.core.validation import KindOfCSV
from energybench.core.utilities import sum_columns
from energybench.io.reading import read_csv
from energybench.io.writing import save_dataframe
from energybench.core.configuration import get_variable_config, VARIABLE_ORDER


SeriesType = Literal["indicator", "adjusted", "target"]


def _compare_single_variable(
    series1: SeriesType,
    series2: SeriesType,
    variable: str,
    start: Timestamp,
    end: Timestamp,
    indicator_csv: Path | None,
    adjusted_csv: Path | None,
    target_csv: Path | None,
    kind_of_adjusted: KindOfCSV,
    indicator_time_column: str,
    target_time_column: str,
    adjusted_time_column: str,
    quiet: bool = False,
) -> dict:
    """Run comparison for a single variable and return the results row."""
    cfg = get_variable_config(variable)

    def load_series(series_type: str) -> pd.Series:
        if series_type == "indicator":
            df = read_csv(
                indicator_csv, start=start, end=end, time_column=indicator_time_column,
            )
            return sum_columns(df, cfg["indicator_types_present"], "indicator")

        if series_type == "adjusted":
            df = pd.read_csv(adjusted_csv, parse_dates=[adjusted_time_column])
            df = df.set_index(adjusted_time_column).loc[start:end]
            col_map = {
                KindOfCSV.benchmarked: cfg["benchmarked_column"],
                KindOfCSV.scaled: cfg["scaled_column"],
                KindOfCSV.ukf: cfg["output_column"],
            }
            return df[col_map[kind_of_adjusted]].rename("adjusted")

        df = read_csv(
            target_csv, start=start.normalize(), end=end.normalize(), time_column=target_time_column,
        )
        return sum_columns(df, cfg["target_types_present"], "target")

    s1 = load_series(series1)
    s2 = load_series(series2)
    s1_daily = s1.resample("D").sum()
    s2_daily = s2.resample("D").sum()

    metrics = compare_series(s1_daily, s2_daily)

    bias_pct = (
        (metrics.mean_a / metrics.mean_b - 1.0) * 100.0
        if metrics.mean_b not in (0, None)
        else float("nan")
    )

    if not quiet:
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

    return {
        "comparison": f"{series1}_vs_{series2}",
        "variable": variable,
        "category": cfg["label"],
        "start": start,
        "end": end,
        "n_days": len(s1_daily),
        **metrics.to_dict(),
        "bias_pct": bias_pct,
    }


def compare_series_unified(
    series1: SeriesType,
    series2: SeriesType,
    variable: str,
    start: Timestamp,
    end: Timestamp,
    indicator_csv: Path | None = None,
    adjusted_csv: Path | None = None,
    target_csv: Path | None = None,
    kind_of_adjusted: KindOfCSV = KindOfCSV.benchmarked,
    output_csv: Path | None = None,
    indicator_time_column: str = "DateTime",
    target_time_column: str = "Date",
    adjusted_time_column: str = "DateTime",
    quiet: bool = False,
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
        Energy type or "all" for all types (e.g., "river", "nuclear", "all").
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
        Type of adjusted series to use (benchmarked, scaled, or ukf).
    output_csv : Path, optional
        Path to save comparison metrics CSV. If None, metrics are not saved.
    indicator_time_column : str, default="DateTime"
        Name of datetime column in indicator CSV.
    target_time_column : str, default="Date"
        Name of datetime column in target CSV.
    adjusted_time_column : str, default="DateTime"
        Name of datetime column in adjusted CSV.
    quiet : bool, default=False
        Suppress all console output.

    Returns
    -------
    pd.DataFrame
        DataFrame with comparison metrics including correlation, error metrics,
        and summary statistics.
    """
    if series1 == series2:
        raise ValueError(f"Cannot compare series with itself: {series1}")

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

    variables_to_process = VARIABLE_ORDER if variable == "all" else [variable]

    all_rows = []
    for var_key in variables_to_process:
        row = _compare_single_variable(
            series1=series1,
            series2=series2,
            variable=var_key,
            start=start,
            end=end,
            indicator_csv=indicator_csv,
            adjusted_csv=adjusted_csv,
            target_csv=target_csv,
            kind_of_adjusted=kind_of_adjusted,
            indicator_time_column=indicator_time_column,
            target_time_column=target_time_column,
            adjusted_time_column=adjusted_time_column,
            quiet=quiet,
        )
        all_rows.append(row)

    result_df = pd.DataFrame(all_rows)

    if output_csv:
        preferred_order = [
            "comparison",
            "variable",
            "category",
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
        cols = [c for c in preferred_order if c in result_df.columns] + [
            c for c in result_df.columns if c not in preferred_order
        ]
        result_df = result_df[cols]

        # Prefix filename with variable for consistency (e.g., river_indicator_vs_target...csv)
        output_name = output_csv
        if variable != "all":
            output_name = Path(f"{variable}_{output_csv.name}")
        save_dataframe(
            df=result_df,
            filename=output_name,
            output_dir=Path("output"),
            variable=variable if variable != "all" else "all",
            index=False,
            quiet=quiet,
        )

    return
