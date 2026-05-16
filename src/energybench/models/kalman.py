from __future__ import annotations

import numpy as np
import pandas as pd


def kalman_filter_1d(
    observations: pd.Series,
    process_variance: float = 0.05,
    observation_variance: float = 0.20,
    initial_state: float | None = None,
    initial_variance: float = 1.0,
) -> pd.Series:
    """
    Simple 1D Kalman filter with random-walk state model.

    State:
        x_t = x_{t-1} + w_t
    Observation:
        y_t = x_t + v_t

    Parameters
    ----------
    observations
        Hourly noisy indicator series.
    process_variance
        Variance of state noise.
    observation_variance
        Variance of observation noise.
    initial_state
        Initial latent state. Defaults to first non-null observation.
    initial_variance
        Initial state variance.

    Returns
    -------
    pd.Series
        Filtered hourly state estimate.
    """
    y = observations.astype(float).copy()

    if initial_state is None:
        first_valid = y.dropna()
        if first_valid.empty:
            raise ValueError("observations contains no valid values.")
        initial_state = float(first_valid.iloc[0])

    x_prev = float(initial_state)
    p_prev = float(initial_variance)

    filtered = []

    for value in y:
        x_pred = x_prev
        p_pred = p_prev + process_variance

        if pd.isna(value):
            x_filt = x_pred
            p_filt = p_pred
        else:
            innovation = float(value) - x_pred
            s = p_pred + observation_variance
            k = p_pred / s
            x_filt = x_pred + k * innovation
            p_filt = (1.0 - k) * p_pred

        filtered.append(x_filt)
        x_prev = x_filt
        p_prev = p_filt

    print(f"> Kalman-filtered the '{observations.name}' time series")

    return pd.Series(filtered, index=observations.index, name="kalman_filtered")


def reconcile_to_daily_totals(
    hourly_series: pd.Series,
    daily_reference: pd.Series,
    preserve_nonnegativity: bool = True,
) -> pd.Series:
    """
    Rescale each day of an hourly series so the daily sum matches the reference exactly.
    """
    hourly = hourly_series.astype(float).copy()
    out = []

    for day, group in hourly.groupby(hourly.index.normalize()):
        if day not in daily_reference.index:
            continue

        target = float(daily_reference.loc[day])
        current = float(group.sum())

        if current == 0 or np.isnan(current):
            adjusted = pd.Series(np.nan, index=group.index)
        else:
            factor = target / current
            adjusted = group * factor

        if preserve_nonnegativity:
            adjusted = adjusted.clip(lower=0)

            adjusted_sum = float(adjusted.sum())
            if adjusted_sum > 0:
                adjusted = adjusted * (target / adjusted_sum)

        out.append(adjusted)

    if not out:
        return pd.Series(dtype=float, name="hourly_reconciled")

    result = pd.concat(out).sort_index()
    result.name = "hourly_reconciled"

    print(f"> Rescaled the '{hourly_series.name}' time series")

    return result
