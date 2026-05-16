from pathlib import Path
import numpy as np
import pandas as pd
from pandas import DataFrame, Series


def temporal_disaggregate_sfoe_daily_to_15min(
    daily_type_series: pd.Series,
    swissgrid_15min_total: pd.Series,
    electricity_generation_type: str,
    method: str = "proportional",
    alpha: float = 0.85,
    min_value: float = 0.0,
    output_directory: Path = Path("output"),
    output_filename: Path | None = None,
) -> pd.DataFrame:
    """
    Disaggregate a daily target source per-type series to 15-minute values using Swissgrid totals
    as a temporal indicator.

    Parameters
    ----------
    daily_type_series : pd.Series
        Daily target source totals for one generation type.
        Index must be datetime-like at daily frequency.
    swissgrid_15min_total : pd.Series
        Swissgrid 15-minute total production series.
        Index must be datetime-like at 15-minute frequency.
    electricity_generation_type : str
        Name of the generation type.
    method : str
        "proportional" or "hybrid".
        - proportional: use Swissgrid daily shape only.
        - hybrid: blend Swissgrid shape with a flat daily profile.
    alpha : float
        Weight for Swissgrid shape in hybrid mode.
    min_value : float
        Lower bound for output values.
    output_directory : Path
        Output folder.
    output_filename : Path | None
        Optional CSV filename.

    Returns
    -------
    pd.DataFrame
        15-minute disaggregated series with metadata.
    """
    daily_type_series = daily_type_series.sort_index().astype(float)
    swissgrid_15min_total = swissgrid_15min_total.sort_index().astype(float)

    out = []

    for day, target_daily_total in daily_type_series.items():
        day = pd.Timestamp(day).normalize()
        mask = swissgrid_15min_total.index.normalize() == day
        day_shape = swissgrid_15min_total.loc[mask].copy()

        if day_shape.empty:
            idx = pd.date_range(day, periods=96, freq="15min")
            weights = pd.Series(1.0 / len(idx), index=idx)
        else:
            weights = day_shape.clip(lower=min_value)
            s = weights.sum(skipna=True)

            if s <= 0 or np.isnan(s):
                idx = day_shape.index
                weights = pd.Series(1.0 / len(idx), index=idx)
            else:
                weights = weights / s

        if method == "hybrid":
            idx = weights.index
            flat = pd.Series(1.0 / len(idx), index=idx)
            weights = alpha * weights + (1.0 - alpha) * flat
            weights = weights / weights.sum()

        values = weights * float(target_daily_total)

        if min_value is not None:
            values = values.clip(lower=min_value)
            diff = float(target_daily_total) - values.sum()
            if abs(diff) > 1e-12 and len(values) > 0:
                free = values > min_value
                if free.any():
                    values.loc[free] += diff / free.sum()

        out.append(values)

    result = pd.concat(out).sort_index().rename(electricity_generation_type)

    df = result.to_frame()
    df.index.name = "DateTime"
    df["date"] = df.index.normalize().date
    df["hour"] = df.index.hour
    df["minute"] = df.index.minute
    df["generation_type"] = electricity_generation_type
    df["source_daily"] = "target source"
    df["source_indicator"] = "Swissgrid"
    df["method"] = method

    output_directory.mkdir(parents=True, exist_ok=True)
    if output_filename is None:
        output_filename = Path(f"{electricity_generation_type.lower()}_sfoe_daily_to_15min.csv")
    elif output_filename.suffix != ".csv":
        output_filename = output_filename.with_suffix(".csv")

    output_path = output_directory / output_filename
    df.to_csv(output_path, index=True, date_format="%Y-%m-%d %H:%M:%S")

    print(f"💾 Saved temporal disaggregation to '{output_path}'")
    return df
