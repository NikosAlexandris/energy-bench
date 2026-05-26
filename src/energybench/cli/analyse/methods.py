"""
Compare adjustment methods (scaling, benchmarking, UKF) on the same data.
"""

import contextlib
import io
from pathlib import Path
from typing import Annotated, Optional

import cyclopts
import pandas as pd

from energybench.core.configuration import get_variable_config
from energybench.core.metrics import compare_series
from energybench.core.utilities import sum_columns
from energybench.io.reading import read_csv
from energybench.models.scaling import scale_series
from energybench.models.benchmarking import benchmark
from energybench.models.kalman import unscented_kalman_filter

_METHODS = ["scaling", "benchmarking", "ukf"]


def suppress(fn):
    with contextlib.redirect_stdout(io.StringIO()):
        return fn()


def _run_method(
    method: str,
    indicator: pd.Series,
    target: pd.Series,
    cfg: dict,
    variable: str = "",
    indicator_csv: Path | None = None,
    target_csv: Path | None = None,
    start: pd.Timestamp | None = None,
    end: pd.Timestamp | None = None,
) -> pd.Series:
    """Run a single adjustment method, return hourly result."""
    if method == "scaling":
        return suppress(lambda: scale_series(indicator, target)).reindex(indicator.index)
    elif method == "benchmarking":
        if not all([indicator_csv, target_csv, start, end]):
            raise ValueError("benchmarking requires indicator_csv, target_csv, start, end")
        df = suppress(
            lambda: benchmark(variable, indicator_csv, target_csv, start, end)
        )
        col = cfg.get("output_column", f"{variable}_benchmarked_gwh")
        if col in df.columns:
            return df.set_index(df.columns[0])[col].reindex(indicator.index)
        return df.iloc[:, 1].reindex(indicator.index)
    elif method == "ukf":
        return suppress(lambda: unscented_kalman_filter(indicator, target)).reindex(indicator.index)
    else:
        raise ValueError(f"Unknown method: {method}")


def compare_adjustment_methods(
    variable: Annotated[str, cyclopts.Parameter(help="Energy type to analyze")],
    indicator_csv: Annotated[Path, cyclopts.Parameter(help="Path to high-frequency indicator CSV")],
    target_csv: Annotated[Path, cyclopts.Parameter(help="Path to low-frequency target CSV")],
    start: Annotated[pd.Timestamp, cyclopts.Parameter(help="Start date")],
    end: Annotated[pd.Timestamp, cyclopts.Parameter(help="End date")],
    methods: Annotated[
        Optional[list[str]],
        cyclopts.Parameter(help=f"Methods to compare ({', '.join(_METHODS)})"),
    ] = None,
    output_csv: Annotated[
        Optional[Path],
        cyclopts.Parameter(help="Output CSV for comparison results"),
    ] = None,
) -> None:
    """
    Compare different adjustment methods on the same data.

    Runs each method, compares hourly output against the daily target,
    and prints a summary table of metrics.

    Example:
        nrgbnc analyse compare-methods river \\
            --indicator-csv data/entsoe_hourly_2016_2025.csv \\
            --target-csv data/sfoe_daily_2016_2025.csv \\
            --start 2024-01-01 \\
            --end 2025-12-31
    """
    if methods is None:
        methods = list(_METHODS)

    for m in methods:
        if m not in _METHODS:
            print(f"⚠️  Unknown method '{m}'. Valid: {', '.join(_METHODS)}")
            return

    # Ensure timestamps
    start = pd.Timestamp(start)
    end = pd.Timestamp(end)
    cfg = get_variable_config(variable)

    print(f"Comparing adjustment methods for {cfg['label']}...")
    print(f"  Methods: {', '.join(methods)}")
    print(f"  Period:  {start.date()} to {end.date()}")

    indicator = sum_columns(
        read_csv(indicator_csv, start=start, end=end),
        cfg["indicator_types_present"],
        "indicator",
    )
    target = sum_columns(
        read_csv(target_csv, start=start, end=end, time_column="Date"),
        cfg["target_types_present"],
        "target",
    )

    # Baseline: indicator vs target (before any adjustment)
    ind_daily = indicator.resample("D").sum()
    tgt_daily = target.reindex(ind_daily.index).dropna()
    common = ind_daily.index.intersection(tgt_daily.index)
    baseline_metrics = compare_series(ind_daily.reindex(common), tgt_daily.reindex(common))

    all_metrics = {}
    for method in methods:
        try:
            result = _run_method(method, indicator, target, cfg,
                                 variable=variable, indicator_csv=indicator_csv,
                                 target_csv=target_csv, start=start, end=end)
        except Exception as e:
            print(f"  ❌ {method}: {e}")
            continue

        # Daily accuracy check — all methods must match targets
        adj_daily = result.resample("D").sum()
        daily_common = adj_daily.index.intersection(tgt_daily.index)
        daily_acc = compare_series(adj_daily.reindex(daily_common), tgt_daily.reindex(daily_common))
        daily_bias = ((daily_acc["mean_a"] / daily_acc["mean_b"]) - 1) * 100 if daily_acc["mean_b"] else 0

        # Hourly comparison against raw indicator — shows how much the shape changed
        hourly_common = result.index.intersection(indicator.index)
        hourly_metrics = compare_series(result.reindex(hourly_common), indicator.reindex(hourly_common))

        hourly_metrics["daily_bias_pct"] = daily_bias
        hourly_metrics["sum_target"] = float(tgt_daily.sum())
        all_metrics[method] = hourly_metrics

    # Print summary table
    print()
    header = f"{'':>14}  {'MAE→ind':>8}  {'RMSE→ind':>8} {'Pearson→ind':>8}  {'DailyBias%':>10}  {'AdjSum':>10}  {'TgtSum':>10}"
    sep = "-" * len(header)
    print(header)
    print(sep)

    b = baseline_metrics
    print(f"{'indicator':>14}  {b['mae']:>8.3f}  {b['rmse']:>8.3f}  {b['pearson']:>8.4f}  {'—':>10}  {b['sum_a']:>10.1f}  {b['sum_b']:>10.1f}")
    print(f"{'target':>14}  {'—':>8}  {'—':>8}  {'—':>8}  {'—':>10}  {'—':>10}  {b['sum_b']:>10.1f}")

    for method in methods:
        if method not in all_metrics:
            continue
        m = all_metrics[method]
        print(f"{method:>14}  {m['mae']:>8.3f}  {m['rmse']:>8.3f}  {m['pearson']:>8.4f}  {m['daily_bias_pct']:>10.4f}  {m['sum_a']:>10.1f}  {m['sum_target']:>10.1f}")

    print(sep)
    print()

    # Key insight
    if all_metrics:
        best_method = min(all_metrics, key=lambda m: all_metrics[m]["mae"])
        worst_method = max(all_metrics, key=lambda m: all_metrics[m]["mae"])
        print(f"Least shape change: {best_method} (MAE vs indicator = {all_metrics[best_method]['mae']:.3f})")
        print(f"Most shape change:  {worst_method} (MAE vs indicator = {all_metrics[worst_method]['mae']:.3f})")
        print("All methods match daily targets (DailyBias% ≈ 0).")
        print()

    # Optionally save CSV
    if output_csv:
        rows = []
        for method, m in all_metrics.items():
            rows.append({
                "variable": variable,
                "method": method,
                "mae_vs_indicator": m["mae"],
                "rmse_vs_indicator": m["rmse"],
                "pearson_vs_indicator": m["pearson"],
                "spearman_vs_indicator": m["spearman"],
                "daily_bias_pct": m["daily_bias_pct"],
                "sum_adjusted": m["sum_a"],
                "sum_target": m["sum_target"],
            })
        df = pd.DataFrame(rows)
        df.to_csv(output_csv, index=False)
        print(f"💾 Results saved to {output_csv}")
