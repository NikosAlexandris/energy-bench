from typing import Optional
from energybench.core.utilities import sum_columns
from energybench.core.metrics import _to_series, compare_series
import pandas as pd
from pandas import Timestamp
import numpy as np


def expand_daily_to_hourly_flat(
    daily: pd.Series,
    hourly_index: pd.DatetimeIndex,
) -> pd.Series:
    out = daily.reindex(hourly_index, method="ffill") / 24.0
    out.name = f"{daily.name}_flat_hourly"
    return out


def compute_comparison_row(
    indicator_data: pd.DataFrame,
    target_data: pd.DataFrame,
    spec: dict,
    start: Timestamp,
    end: Timestamp,
) -> tuple[pd.Series, pd.Series, dict]:
    """ """
    hourly = sum_columns(
        indicator_data,
        spec["hf_columns"],
        output_name=f"{spec['key']}_hourly",
        # factor=1 / 1000.0,  # MW -> GWh for hourly energy
    ).loc[start:end]

    hourly_daily = hourly.resample("D").sum()

    daily = sum_columns(
        target_data,
        spec["lf_columns"],
        output_name=f"{spec['key']}_daily",
    ).loc[start:end]

    daily_hourly_flat = expand_daily_to_hourly_flat(daily, hourly.index)

    daily_metrics = compare_series(hourly_daily, daily)
    shape_metrics = compare_intraday_shape(hourly, daily_hourly_flat)

    row = {
        "category": spec["key"],
        "label_daily": spec["label_daily"],
        "label_shape": spec["label_shape"],
        "start": pd.Timestamp(start),
        "end": pd.Timestamp(end),
        **daily_metrics.to_dict(),
        **shape_metrics.to_dict(),
    }

    if "mean_a" in row and "mean_b" in row and row["mean_b"] not in (0, None):
        row["bias_pct"] = (row["mean_a"] / row["mean_b"] - 1.0) * 100.0
    else:
        row["bias_pct"] = float("nan")

    return daily_metrics, shape_metrics, row


def shape_similarity_daily_profiles(
    x: pd.Series | pd.DataFrame,
    value_col: Optional[str] = None,
    normalize: str = "sum",
) -> pd.DataFrame:
    """
    Compute normalized daily profiles from wide-format hourly/daily CSVs.

    No pivot needed — works directly with your DateTime-indexed wide data.
    """
    s = _to_series(x, value_col=value_col).dropna()

    df = pd.DataFrame({"value": s})
    df["date"] = df.index.normalize()
    df["hour"] = df.index.hour

    # Direct groupby instead of pivot — handles duplicates gracefully
    daily_profiles = df.groupby(["date", "hour"])["value"].sum().unstack(fill_value=0)

    if normalize == "sum":
        daily_profiles = daily_profiles.div(daily_profiles.sum(axis=1), axis=0)
    elif normalize == "max":
        daily_profiles = daily_profiles.div(daily_profiles.max(axis=1), axis=0)
    elif normalize is not None:
        raise ValueError("normalize must be 'sum', 'max', or None")

    return daily_profiles.sort_index()


def compare_intraday_shape(
    a: pd.Series | pd.DataFrame,
    b: pd.Series | pd.DataFrame,
    value_col_a: Optional[str] = None,
    value_col_b: Optional[str] = None,
    normalize: str = "sum",
    skip_zero_std: bool = True,
) -> pd.Series:
    """ """
    wa = shape_similarity_daily_profiles(a, value_col=value_col_a, normalize=normalize)
    wb = shape_similarity_daily_profiles(b, value_col=value_col_b, normalize=normalize)

    common = wa.index.intersection(wb.index)
    wa = wa.loc[common]
    wb = wb.loc[common]

    if wa.empty:
        raise ValueError("No common days for intraday shape comparison")

    day_corrs = []
    day_maes = []

    for day in common:
        xa = wa.loc[day].dropna()
        xb = wb.loc[day].dropna()
        mask = xa.notna() & xb.notna()
        xa = xa[mask]
        xb = xb[mask]
        if len(xa) < 2:
            continue
        day_corrs.append(xa.corr(xb))
        day_maes.append((xa - xb).abs().mean())

        # Skip if zero std (perfectly flat day)
        if skip_zero_std and (xa.std() == 0 or xb.std() == 0):
            continue

        day_corrs.append(xa.corr(xb))
        day_maes.append((xa - xb).abs().mean())

    return pd.Series(
        {
            "n_days": len(common),
            "mean_daily_shape_corr": (float(np.nanmean(day_corrs)) if day_corrs else np.nan),
            "median_daily_shape_corr": (float(np.nanmedian(day_corrs)) if day_corrs else np.nan),
            "mean_daily_shape_mae": float(np.nanmean(day_maes)) if day_maes else np.nan,
            "median_daily_shape_mae": (float(np.nanmedian(day_maes)) if day_maes else np.nan),
        }
    )
