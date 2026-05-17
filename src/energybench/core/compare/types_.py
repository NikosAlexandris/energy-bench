from __future__ import annotations

from pathlib import Path
import pandas as pd

from energybench.core.configuration import get_variable_config


def compare_series_types(
    variable: str,
    indicator_csv: Path,
    target_csv: Path,
    start: pd.Timestamp,
    end: pd.Timestamp,
    indicator_time_column: str = "DateTime",
    target_time_column: str = "Date",
) -> pd.DataFrame:
    """
    Compare energy types between indicator and target data sources.
    
    Args:
        variable: Energy type to compare
        indicator_csv: Path to high-frequency indicator CSV
        target_csv: Path to low-frequency target CSV
        start: Start timestamp for comparison period
        end: End timestamp for comparison period
        indicator_time_column: Name of datetime column in indicator CSV
        target_time_column: Name of datetime column in target CSV
        
    Returns:
        DataFrame with daily comparison metrics
    """
    cfg = get_variable_config(variable)

    indicator_df = pd.read_csv(indicator_csv, parse_dates=[indicator_time_column])
    target_df = pd.read_csv(target_csv, parse_dates=[target_time_column])

    indicator_df = indicator_df.set_index(indicator_time_column).loc[start:end]
    target_df = target_df.set_index(target_time_column).loc[start.normalize() : end.normalize()]

    indicator_cols = [c for c in cfg["indicator_types"] if c in indicator_df.columns]
    target_cols = [c for c in cfg["target_types"] if c in target_df.columns]

    if not indicator_cols:
        raise ValueError(
            f"No indicator columns found for {variable}: {cfg['indicator_types']}"
        )
    if not target_cols:
        raise ValueError(f"No target columns found for {variable}: {cfg['target_types']}")

    indicator_daily = indicator_df[indicator_cols].apply(pd.to_numeric, errors="coerce").sum(axis=1).resample("D").sum()
    target_daily = target_df[target_cols].apply(pd.to_numeric, errors="coerce").sum(axis=1)

    out = pd.DataFrame(
        {
            "indicator_daily_sum_gwh": indicator_daily,
            "target_daily_gwh": target_daily,
        }
    ).sort_index()

    out["difference_gwh"] = out["target_daily_gwh"] - out["indicator_daily_sum_gwh"]
    out["relative_difference_pct"] = out["difference_gwh"] / out["target_daily_gwh"] * 100.0

    return out.reset_index(names="Date")
