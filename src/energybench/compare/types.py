from __future__ import annotations

from pathlib import Path
import pandas as pd

from energybench.variables import get_variable_config


def compare_types(
    variable: str,
    high_frequency_csv: Path,
    low_frequency_csv: Path,
    start: pd.Timestamp,
    end: pd.Timestamp,
    high_frequency_datetime_column: str = "DateTime",
    low_frequency_date_column: str = "Date",
) -> pd.DataFrame:
    cfg = get_variable_config(variable)

    hf = pd.read_csv(high_frequency_csv, parse_dates=[high_frequency_datetime_column])
    lf = pd.read_csv(low_frequency_csv, parse_dates=[low_frequency_date_column])

    hf = hf.set_index(high_frequency_datetime_column).loc[start:end]
    lf = lf.set_index(low_frequency_date_column).loc[start.normalize():end.normalize()]

    hf_cols = [c for c in cfg["indicator_columns"] if c in hf.columns]
    lf_cols = [c for c in cfg["target_columns"] if c in lf.columns]

    if not hf_cols:
        raise ValueError(f"No high-frequency columns found for {variable}: {cfg['indicator_columns']}")
    if not lf_cols:
        raise ValueError(f"No low-frequency columns found for {variable}: {cfg['target_columns']}")

    hourly_daily = hf[hf_cols].apply(pd.to_numeric, errors="coerce").sum(axis=1).resample("D").sum()
    daily_ref = lf[lf_cols].apply(pd.to_numeric, errors="coerce").sum(axis=1)

    out = pd.DataFrame({
        "hourly_daily_sum_gwh": hourly_daily,
        "daily_reference_gwh": daily_ref,
    }).sort_index()

    out["difference_gwh"] = out["daily_reference_gwh"] - out["hourly_daily_sum_gwh"]
    out["relative_difference_pct"] = (
        out["difference_gwh"] / out["daily_reference_gwh"] * 100.0
    )

    return out.reset_index(names="Date")
