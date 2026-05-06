from __future__ import annotations

import pandas as pd


def build_daily_validation(
    original_hourly: pd.Series,
    filtered_hourly: pd.Series,
    reconciled_hourly: pd.Series,
    daily_reference: pd.Series,
) -> pd.DataFrame:
    """
    """
    print("> Building daily validation...")
    original_daily = original_hourly.resample("D").sum().rename("original_daily")
    filtered_daily = filtered_hourly.resample("D").sum().rename("filtered_daily")
    reconciled_daily = reconciled_hourly.resample("D").sum().rename("reconciled_daily")
    target_daily = daily_reference.rename("target_daily")

    df = pd.concat(
        [original_daily, filtered_daily, reconciled_daily, target_daily],
        axis=1,
    ).sort_index()

    df["original_minus_target"] = df["original_daily"] - df["target_daily"]
    df["filtered_minus_target"] = df["filtered_daily"] - df["target_daily"]
    df["reconciled_minus_target"] = df["reconciled_daily"] - df["target_daily"]

    return df
