from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Optional

import numpy as np
import pandas as pd


@dataclass
class SeriesSummary:
    name: str
    n: int
    n_missing: int
    start: Optional[pd.Timestamp]
    end: Optional[pd.Timestamp]
    mean: float
    std: float
    min: float
    q05: float
    q25: float
    median: float
    q75: float
    q95: float
    max: float
    sum: float
    ramp_mean_abs: float
    ramp_p95_abs: float
    lag1_autocorr: float


def _to_series(
    x: pd.Series | pd.DataFrame,
    value_col: Optional[str] = None,
    time_col: Optional[str] = None,
    name: Optional[str] = None,
) -> pd.Series:
    if isinstance(x, pd.Series):
        s = x.copy()
    else:
        if value_col is None:
            raise ValueError("value_col is required when x is a DataFrame")
        if time_col is not None:
            s = x.set_index(time_col)[value_col].copy()
        else:
            s = x[value_col].copy()

    if not isinstance(s.index, pd.DatetimeIndex):
        try:
            s.index = pd.to_datetime(s.index)
        except Exception as e:
            raise ValueError("Series index must be DatetimeIndex or convertible to datetime") from e

    s = pd.to_numeric(s, errors="coerce").sort_index()
    if name is not None:
        s.name = name
    elif s.name is None:
        s.name = "series"
    return s


def describe_series(s: pd.Series) -> SeriesSummary:
    s = _to_series(s)
    v = s.dropna()

    ramps = v.diff().dropna().abs()
    lag1 = v.autocorr(lag=1) if len(v) > 2 else np.nan

    return SeriesSummary(
        name=s.name or "series",
        n=len(s),
        n_missing=int(s.isna().sum()),
        start=s.index.min() if len(s) else None,
        end=s.index.max() if len(s) else None,
        mean=float(v.mean()) if len(v) else np.nan,
        std=float(v.std()) if len(v) else np.nan,
        min=float(v.min()) if len(v) else np.nan,
        q05=float(v.quantile(0.05)) if len(v) else np.nan,
        q25=float(v.quantile(0.25)) if len(v) else np.nan,
        median=float(v.median()) if len(v) else np.nan,
        q75=float(v.quantile(0.75)) if len(v) else np.nan,
        q95=float(v.quantile(0.95)) if len(v) else np.nan,
        max=float(v.max()) if len(v) else np.nan,
        sum=float(v.sum()) if len(v) else np.nan,
        ramp_mean_abs=float(ramps.mean()) if len(ramps) else np.nan,
        ramp_p95_abs=float(ramps.quantile(0.95)) if len(ramps) else np.nan,
        lag1_autocorr=float(lag1) if pd.notna(lag1) else np.nan,
    )


def align_series(
    a: pd.Series,
    b: pd.Series,
    join: str = "inner",
) -> pd.DataFrame:
    a = _to_series(a)
    b = _to_series(b)

    df = pd.concat([a.rename("a"), b.rename("b")], axis=1, join=join).sort_index()
    return df


def resample_pair(
    a: pd.Series,
    b: pd.Series,
    freq: str,
    agg: str = "sum",
    join: str = "inner",
) -> pd.DataFrame:
    a = _to_series(a)
    b = _to_series(b)

    if agg == "sum":
        a2 = a.resample(freq).sum()
        b2 = b.resample(freq).sum()
    elif agg == "mean":
        a2 = a.resample(freq).mean()
        b2 = b.resample(freq).mean()
    elif agg == "median":
        a2 = a.resample(freq).median()
        b2 = b.resample(freq).median()
    else:
        raise ValueError(f"Unsupported agg={agg}")

    df = pd.concat([a2.rename("a"), b2.rename("b")], axis=1, join=join).sort_index()
    return df.dropna()


def _safe_mean(x: pd.Series) -> float:
    return float(x.mean()) if len(x) else np.nan


def _safe_std(x: pd.Series) -> float:
    return float(x.std()) if len(x) else np.nan


def pearson_corr(x: pd.Series, y: pd.Series) -> float:
    if len(x) < 2:
        return np.nan
    return float(x.corr(y, method="pearson"))


def spearman_corr(x: pd.Series, y: pd.Series) -> float:
    if len(x) < 2:
        return np.nan
    return float(x.corr(y, method="spearman"))


def cosine_similarity(x: pd.Series, y: pd.Series) -> float:
    xv = x.to_numpy(dtype=float)
    yv = y.to_numpy(dtype=float)
    mask = np.isfinite(xv) & np.isfinite(yv)
    xv = xv[mask]
    yv = yv[mask]
    if len(xv) == 0:
        return np.nan
    nx = np.linalg.norm(xv)
    ny = np.linalg.norm(yv)
    if nx == 0 or ny == 0:
        return np.nan
    return float(np.dot(xv, yv) / (nx * ny))


def mae(x: pd.Series, y: pd.Series) -> float:
    return float((x - y).abs().mean())


def rmse(x: pd.Series, y: pd.Series) -> float:
    return float(np.sqrt(((x - y) ** 2).mean()))


def mbe(x: pd.Series, y: pd.Series) -> float:
    return float((x - y).mean())


def nrmse_mean(x: pd.Series, y: pd.Series) -> float:
    denom = float(y.mean())
    if denom == 0 or np.isnan(denom):
        return np.nan
    return float(np.sqrt(((x - y) ** 2).mean()) / denom)


def smape(x: pd.Series, y: pd.Series) -> float:
    denom = (x.abs() + y.abs()) / 2.0
    z = (x - y).abs() / denom.replace(0, np.nan)
    return float(z.mean())


def wasserstein_1d(x: pd.Series, y: pd.Series) -> float:
    try:
        from scipy.stats import wasserstein_distance
    except ImportError as e:
        raise ImportError("scipy is required for wasserstein_1d") from e

    xv = x.dropna().to_numpy(dtype=float)
    yv = y.dropna().to_numpy(dtype=float)
    if len(xv) == 0 or len(yv) == 0:
        return np.nan
    return float(wasserstein_distance(xv, yv))


def lagged_correlation(
    x: pd.Series,
    y: pd.Series,
    max_lag: int = 48,
) -> pd.DataFrame:
    x = x.copy()
    y = y.copy()

    rows = []
    for lag in range(-max_lag, max_lag + 1):
        if lag < 0:
            corr = x.corr(y.shift(-lag))
        else:
            corr = x.shift(lag).corr(y)
        rows.append({"lag": lag, "pearson": corr})

    out = pd.DataFrame(rows)
    out["abs_pearson"] = out["pearson"].abs()
    return out.sort_values("lag").reset_index(drop=True)


def compare_series(
    a: pd.Series,
    b: pd.Series,
    scale_to: Optional[str] = None,
    allow_shift: bool = False,
    max_lag: int = 48,
) -> pd.Series:
    df = align_series(a, b).dropna()
    if df.empty:
        raise ValueError(
            "No overlapping non-missing values after alignment ! Check your input's temporal extent maybe ?"
        )

    x = df["a"].copy()
    y = df["b"].copy()

    if scale_to == "mean":
        if x.mean() != 0:
            x = x * (y.mean() / x.mean())
    elif scale_to == "sum":
        if x.sum() != 0:
            x = x * (y.sum() / x.sum())
    elif scale_to is not None:
        raise ValueError("scale_to must be None, 'mean', or 'sum'")

    best_lag = 0
    best_corr = pearson_corr(x, y)

    if allow_shift:
        lags = lagged_correlation(x, y, max_lag=max_lag)
        best = lags.loc[lags["abs_pearson"].idxmax()]
        best_lag = int(best["lag"])
        best_corr = float(best["pearson"])

    out = pd.Series(
        {
            "n_overlap": len(df),
            "pearson": pearson_corr(x, y),
            "spearman": spearman_corr(x, y),
            "cosine": cosine_similarity(x, y),
            "mbe": mbe(x, y),
            "mae": mae(x, y),
            "rmse": rmse(x, y),
            "nrmse_mean": nrmse_mean(x, y),
            "smape": smape(x, y),
            "mean_a": _safe_mean(x),
            "mean_b": _safe_mean(y),
            "std_a": _safe_std(x),
            "std_b": _safe_std(y),
            "sum_a": float(x.sum()),
            "sum_b": float(y.sum()),
            "best_lag": best_lag,
            "best_lag_corr": best_corr,
        }
    )
    return out


def compare_at_multiple_resolutions(
    a: pd.Series,
    b: pd.Series,
    resolutions: Iterable[str] = ("H", "D", "W"),
    agg: str = "sum",
) -> pd.DataFrame:
    rows = []
    for freq in resolutions:
        df = resample_pair(a, b, freq=freq, agg=agg)
        if df.empty:
            continue
        stats = compare_series(df["a"], df["b"])
        stats["freq"] = freq
        rows.append(stats)

    if not rows:
        return pd.DataFrame()

    out = pd.DataFrame(rows)
    cols = ["freq"] + [c for c in out.columns if c != "freq"]
    return out[cols]
