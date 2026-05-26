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


def unscented_kalman_filter(
    indicator_hourly: pd.Series,
    target_daily: pd.Series,
    alpha: float = 1.0,
    beta: float = 2.0,
    kappa: float = 0.0,
    process_noise: float = 0.001,
    obs_noise: float = 0.01,
) -> pd.Series:
    """
    1D Unscented Kalman Filter for hourly temporal disaggregation in log-space.

    Uses FilterPy's ``UnscentedKalmanFilter`` (MerweScaledSigmaPoints).

    At each hour the 1D state ``z_t = log(generation_t)`` follows the
    indicator's relative change:
        z_t = z_{t-1} + (log I_t - log I_{t-1}) + w,   w ~ N(0, Q)
    and is observed as:
        log I_t = z_t + v,   v ~ N(0, R)

    After filtering, each day is reconciled to the daily target via a uniform
    log-space correction (proportional in linear space).

    Parameters
    ----------
    indicator_hourly
        Hourly indicator series.
    target_daily
        Daily target series.
    alpha, beta, kappa
        UKF scaling parameters (1.0 / 2.0 / 0.0 are optimal for Gaussian).
    process_noise
        Std of process noise (log-space).  Controls how freely the state
        deviates from the indicator's relative changes.  Default 0.001.
    obs_noise
        Std of observation noise in log-space.  How much the indicator is
        trusted as a direct observation of log-generation.  Default 0.01.

    Returns
    -------
    pd.Series
        Hourly estimated generation (linear scale).
    """
    from filterpy.kalman import MerweScaledSigmaPoints, UnscentedKalmanFilter

    indicator = indicator_hourly.astype(float).clip(lower=1e-6)
    target_index = target_daily.index.normalize()
    log_ind = np.log(indicator.values)
    n_hours = len(indicator)

    # State transition: add the indicator's log-delta
    def fx(x, dt, diff_log):
        return x + diff_log

    # Observation: we observe log-indicator directly
    def hx(x):
        return x

    points = MerweScaledSigmaPoints(n=1, alpha=alpha, beta=beta, kappa=kappa)
    ukf = UnscentedKalmanFilter(dim_x=1, dim_z=1, dt=1.0, fx=fx, hx=hx, points=points)

    first = float(indicator.dropna().iloc[0]) if len(indicator) > 0 else 1.0
    ukf.x = np.array([np.log(first)])
    ukf.P *= 0.01
    ukf.R = np.array([[obs_noise ** 2]])
    ukf.Q = np.array([[process_noise ** 2]])

    z = np.empty(n_hours)
    for t in range(n_hours):
        diff_log = 0.0 if t == 0 else log_ind[t] - log_ind[t - 1]
        if not np.isfinite(diff_log):
            diff_log = 0.0
        ukf.predict(dt=1.0, diff_log=diff_log)
        ukf.update(np.atleast_1d(log_ind[t]))
        z[t] = ukf.x[0]

    result = np.exp(z)
    series = pd.Series(result, index=indicator.index, name="ukf_filtered")

    # Reconcile each day to its target
    out = series.copy()
    for day, grp in series.groupby(series.index.normalize()):
        day_dt = pd.Timestamp(day)
        if day_dt not in target_index:
            continue
        target = float(target_daily.loc[day_dt])
        current = float(grp.sum())
        if current > 0:
            factor = target / current
            out.loc[grp.index] = grp * factor

    print(f"> UKF-disaggregated ({len(out)} hours, {len(out) // 24} days)")
    out.name = "ukf_disaggregated"
    return out


# 24D UKF helpers — kept for reference, unused by the default path
def _ukf_sigma_points(mean, cov, lam, n):
    """Generate 2n+1 sigma points for a given mean and covariance."""
    sigma = np.zeros((2 * n + 1, n))
    sigma[0] = mean
    try:
        L = np.linalg.cholesky((n + lam) * cov)
    except np.linalg.LinAlgError:
        L = np.linalg.cholesky((n + lam) * cov + np.eye(n) * 1e-8)
    for i in range(n):
        sigma[i + 1] = mean + L[:, i]
        sigma[n + i + 1] = mean - L[:, i]
    return sigma


def _ukf_update(z_pred, P_pred, target, w_m, w_c, lam, R, n):
    """UKF measurement update with non-linear observation h(z) = sum(exp(z))."""
    sigma = _ukf_sigma_points(z_pred, P_pred, lam, n)
    obs_sigma = np.sum(np.exp(sigma), axis=1)
    obs_mean = np.dot(w_m, obs_sigma)
    obs_diff = obs_sigma - obs_mean
    S = np.dot(w_c * obs_diff, obs_diff) + R
    diff_s = sigma - z_pred
    cross = np.dot(w_c * diff_s.T, obs_diff)
    K = cross / S
    z_upd = z_pred + K * (target - obs_mean)
    P_upd = P_pred - np.outer(K, K) * S
    P_upd = (P_upd + P_upd.T) / 2
    return z_upd, P_upd


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
