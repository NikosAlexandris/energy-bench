"""
Automated bias detection and subperiod analysis for time series.

This module provides tools to:
1. Detect bias patterns using rolling windows
2. Identify changepoints in bias characteristics
3. Cluster periods with similar error patterns
4. Recommend optimal adjustment strategies
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal, Optional

import numpy as np
import pandas as pd
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler

from energybench.core.metrics import compare_series, align_series


@dataclass
class BiasWindow:
    """Represents bias statistics for a time window."""

    start: pd.Timestamp
    end: pd.Timestamp
    n_points: int
    bias_pct: float
    mae: float
    rmse: float
    pearson: float
    mean_indicator: float
    mean_target: float
    std_indicator: float
    std_target: float

    def to_dict(self) -> dict:
        return {
            "start": self.start,
            "end": self.end,
            "n_points": self.n_points,
            "bias_pct": self.bias_pct,
            "mae": self.mae,
            "rmse": self.rmse,
            "pearson": self.pearson,
            "mean_indicator": self.mean_indicator,
            "mean_target": self.mean_target,
            "std_indicator": self.std_indicator,
            "std_target": self.std_target,
        }


@dataclass
class Changepoint:
    """Represents a detected changepoint in bias characteristics."""

    timestamp: pd.Timestamp
    confidence: float
    metric_changed: str
    value_before: float
    value_after: float
    change_magnitude: float


@dataclass
class SubperiodCluster:
    """Represents a cluster of time periods with similar characteristics."""

    cluster_id: int
    periods: list[tuple[pd.Timestamp, pd.Timestamp]]
    mean_bias_pct: float
    mean_mae: float
    mean_rmse: float
    mean_pearson: float
    n_periods: int
    recommended_method: str
    confidence: float


@dataclass
class SubperiodRecommendation:
    """Recommendation for adjusting a specific subperiod."""

    start: pd.Timestamp
    end: pd.Timestamp
    recommended_method: Literal["scaling", "benchmarking", "kalman"]
    confidence: float
    reason: str
    expected_improvement: dict[str, float]
    cluster_id: Optional[int] = None


@dataclass
class BiasDetectionResult:
    """Complete result of bias detection analysis."""

    variable: str
    overall_bias_pct: float
    overall_mae: float
    overall_rmse: float
    rolling_windows: list[BiasWindow]
    changepoints: list[Changepoint]
    clusters: list[SubperiodCluster]
    recommendations: list[SubperiodRecommendation]
    metadata: dict = field(default_factory=dict)

    def to_dataframe(self) -> pd.DataFrame:
        """Convert recommendations to DataFrame."""
        if not self.recommendations:
            return pd.DataFrame()

        rows = []
        for rec in self.recommendations:
            rows.append(
                {
                    "start": rec.start,
                    "end": rec.end,
                    "method": rec.recommended_method,
                    "confidence": rec.confidence,
                    "reason": rec.reason,
                    "cluster_id": rec.cluster_id,
                    **{f"expected_{k}": v for k, v in rec.expected_improvement.items()},
                }
            )
        return pd.DataFrame(rows)

    def to_summary(self) -> str:
        """Generate human-readable summary."""
        lines = [
            f"Bias Detection Analysis for {self.variable}",
            "=" * 60,
            f"Overall Bias: {self.overall_bias_pct:+.2f}%",
            f"Overall MAE: {self.overall_mae:.4f}",
            f"Overall RMSE: {self.overall_rmse:.4f}",
            "",
            f"Detected {len(self.changepoints)} changepoints",
            f"Identified {len(self.clusters)} distinct bias patterns",
            f"Generated {len(self.recommendations)} subperiod recommendations",
            "",
        ]

        if self.recommendations:
            lines.append("Top Recommendations:")
            lines.append("-" * 60)
            for i, rec in enumerate(self.recommendations[:5], 1):
                lines.append(
                    f"{i}. {rec.start.date()} to {rec.end.date()}: "
                    f"{rec.recommended_method} (confidence: {rec.confidence:.1%})"
                )
                lines.append(f"   Reason: {rec.reason}")
                lines.append("")

        return "\n".join(lines)


def rolling_bias_analysis(
    indicator: pd.Series,
    target: pd.Series,
    window_size: str = "30D",
    step_size: str = "7D",
    min_periods: int = 20,
) -> list[BiasWindow]:
    """
    Analyze bias using rolling windows.

    Parameters
    ----------
    indicator : pd.Series
        High-frequency indicator series (e.g., hourly indicator)
    target : pd.Series
        Low-frequency target series (e.g., daily target)
    window_size : str
        Size of rolling window (pandas offset string)
    step_size : str
        Step between windows (pandas offset string)
    min_periods : int
        Minimum number of points required in window

    Returns
    -------
    list[BiasWindow]
        List of bias statistics for each window
    """
    # Resample indicator to daily BEFORE alignment to ensure proper comparison
    indicator_daily = indicator.resample("D").sum()

    # Now align both daily series
    df = align_series(indicator_daily, target, join="inner").dropna()
    if df.empty:
        return []

    # Both are now daily frequency
    indicator_daily = df["a"]
    target_daily = df["b"]

    windows = []
    start_date = indicator_daily.index.min()
    end_date = indicator_daily.index.max()

    current = start_date
    while current <= end_date:
        window_end = current + pd.Timedelta(window_size)

        ind_window = indicator_daily.loc[current:window_end]
        tgt_window = target_daily.loc[current:window_end]

        if len(ind_window) >= min_periods and len(tgt_window) >= min_periods:
            # Compute comparison metrics
            comparison = compare_series(ind_window, tgt_window)

            # Calculate bias percentage
            mean_ind = float(ind_window.mean())
            mean_tgt = float(tgt_window.mean())
            bias_pct = ((mean_ind / mean_tgt) - 1.0) * 100.0 if mean_tgt != 0 else np.nan

            window = BiasWindow(
                start=current,
                end=window_end,
                n_points=len(ind_window),
                bias_pct=bias_pct,
                mae=comparison["mae"],
                rmse=comparison["rmse"],
                pearson=comparison["pearson"],
                mean_indicator=mean_ind,
                mean_target=mean_tgt,
                std_indicator=float(ind_window.std()),
                std_target=float(tgt_window.std()),
            )
            windows.append(window)

        current += pd.Timedelta(step_size)

    return windows


def detect_changepoints(
    windows: list[BiasWindow],
    metric: str = "bias_pct",
    method: Literal["pelt", "binary_segmentation", "threshold"] = "threshold",
    threshold: float = 5.0,
) -> list[Changepoint]:
    """
    Detect changepoints in bias characteristics.

    Parameters
    ----------
    windows : list[BiasWindow]
        Rolling window results
    metric : str
        Metric to analyze for changepoints
    method : str
        Detection method: 'pelt', 'binary_segmentation', or 'threshold'
    threshold : float
        Threshold for change detection (used with 'threshold' method)

    Returns
    -------
    list[Changepoint]
        Detected changepoints
    """
    if not windows:
        return []

    # Extract metric values
    values = np.array([getattr(w, metric) for w in windows])
    timestamps = [w.start for w in windows]

    changepoints = []

    if method == "threshold":
        # Simple threshold-based detection
        for i in range(1, len(values)):
            change = abs(values[i] - values[i - 1])
            if change > threshold:
                changepoints.append(
                    Changepoint(
                        timestamp=timestamps[i],
                        confidence=min(change / threshold, 1.0),
                        metric_changed=metric,
                        value_before=values[i - 1],
                        value_after=values[i],
                        change_magnitude=change,
                    )
                )

    elif method == "binary_segmentation":
        # Recursive binary segmentation
        def find_best_split(arr: np.ndarray, start_idx: int, end_idx: int) -> Optional[int]:
            if end_idx - start_idx < 4:  # Minimum segment size
                return None

            best_split = None
            best_score = 0

            for split in range(start_idx + 2, end_idx - 1):
                left = arr[start_idx:split]
                right = arr[split:end_idx]

                # Calculate variance reduction
                total_var = np.var(arr[start_idx:end_idx])
                left_var = np.var(left) * len(left) / (end_idx - start_idx)
                right_var = np.var(right) * len(right) / (end_idx - start_idx)
                score = total_var - (left_var + right_var)

                if score > best_score:
                    best_score = score
                    best_split = split

            return best_split if best_score > threshold else None

        def recursive_split(arr: np.ndarray, start_idx: int, end_idx: int):
            split = find_best_split(arr, start_idx, end_idx)
            if split is not None:
                changepoints.append(
                    Changepoint(
                        timestamp=timestamps[split],
                        confidence=0.8,  # Could be refined
                        metric_changed=metric,
                        value_before=float(np.mean(arr[start_idx:split])),
                        value_after=float(np.mean(arr[split:end_idx])),
                        change_magnitude=abs(
                            float(np.mean(arr[split:end_idx]) - np.mean(arr[start_idx:split]))
                        ),
                    )
                )
                recursive_split(arr, start_idx, split)
                recursive_split(arr, split, end_idx)

        recursive_split(values, 0, len(values))
        changepoints.sort(key=lambda x: x.timestamp)

    return changepoints


def cluster_periods(
    windows: list[BiasWindow],
    n_clusters: int = 3,
    features: list[str] = None,
) -> list[SubperiodCluster]:
    """
    Cluster time periods with similar bias characteristics.

    Parameters
    ----------
    windows : list[BiasWindow]
        Rolling window results
    n_clusters : int
        Number of clusters to create
    features : list[str]
        Features to use for clustering

    Returns
    -------
    list[SubperiodCluster]
        Identified clusters
    """
    if not windows or len(windows) < n_clusters:
        return []

    if features is None:
        features = ["bias_pct", "mae", "rmse", "pearson"]

    # Prepare feature matrix
    X = np.array([[getattr(w, f) for f in features] for w in windows])

    # Handle NaN values
    X = np.nan_to_num(X, nan=0.0)

    # Standardize features
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)

    # Perform clustering
    kmeans = KMeans(n_clusters=n_clusters, random_state=42, n_init=10)
    labels = kmeans.fit_predict(X_scaled)

    # Build cluster objects
    clusters = []
    for cluster_id in range(n_clusters):
        mask = labels == cluster_id
        cluster_windows = [w for w, m in zip(windows, mask) if m]

        if not cluster_windows:
            continue

        # Aggregate statistics
        mean_bias = np.mean([w.bias_pct for w in cluster_windows])
        mean_mae = np.mean([w.mae for w in cluster_windows])
        mean_rmse = np.mean([w.rmse for w in cluster_windows])
        mean_pearson = np.mean([w.pearson for w in cluster_windows])

        # Determine recommended method based on characteristics
        if abs(mean_bias) < 5 and mean_pearson > 0.9:
            method = "scaling"
            confidence = 0.9
        elif abs(mean_bias) > 20 or mean_pearson < 0.7:
            method = "benchmarking"
            confidence = 0.8
        else:
            method = "kalman"
            confidence = 0.75

        periods = [(w.start, w.end) for w in cluster_windows]

        cluster = SubperiodCluster(
            cluster_id=cluster_id,
            periods=periods,
            mean_bias_pct=mean_bias,
            mean_mae=mean_mae,
            mean_rmse=mean_rmse,
            mean_pearson=mean_pearson,
            n_periods=len(cluster_windows),
            recommended_method=method,
            confidence=confidence,
        )
        clusters.append(cluster)

    return clusters


def recommend_adjustment_strategy(
    windows: list[BiasWindow],
    changepoints: list[Changepoint],
    clusters: list[SubperiodCluster],
    min_period_days: int = 30,
) -> list[SubperiodRecommendation]:
    """
    Generate recommendations for adjusting specific subperiods.

    Parameters
    ----------
    windows : list[BiasWindow]
        Rolling window results
    changepoints : list[Changepoint]
        Detected changepoints
    clusters : list[SubperiodCluster]
        Period clusters
    min_period_days : int
        Minimum period length for recommendations

    Returns
    -------
    list[SubperiodRecommendation]
        Adjustment recommendations
    """
    recommendations = []

    if not windows:
        return recommendations

    # Create cluster lookup
    cluster_lookup = {}
    for cluster in clusters:
        for start, end in cluster.periods:
            cluster_lookup[(start, end)] = cluster

    # Generate recommendations based on changepoints
    if changepoints:
        # Sort changepoints
        sorted_cps = sorted(changepoints, key=lambda x: x.timestamp)

        # Create periods between changepoints
        periods = []
        start = windows[0].start
        for cp in sorted_cps:
            if (cp.timestamp - start).days >= min_period_days:
                periods.append((start, cp.timestamp))
            start = cp.timestamp

        # Add final period
        end = windows[-1].end
        if (end - start).days >= min_period_days:
            periods.append((start, end))
    else:
        # No changepoints, use cluster-based periods
        periods = []
        for cluster in clusters:
            periods.extend(cluster.periods)

    # Generate recommendations for each period
    for start, end in periods:
        # Find windows in this period
        period_windows = [w for w in windows if start <= w.start < end]

        if not period_windows:
            continue

        # Calculate period statistics
        mean_bias = np.mean([w.bias_pct for w in period_windows])
        mean_pearson = np.mean([w.pearson for w in period_windows])

        # Determine method and confidence
        cluster = cluster_lookup.get((start, end))

        if cluster:
            method = cluster.recommended_method
            confidence = cluster.confidence
            cluster_id = cluster.cluster_id
            reason = f"Part of cluster {cluster_id} with {cluster.n_periods} similar periods"
        else:
            # Fallback logic
            if abs(mean_bias) > 20 or mean_pearson < 0.7:
                method = "benchmarking"
                confidence = 0.8
                reason = f"High bias ({mean_bias:+.1f}%) or low correlation ({mean_pearson:.2f}) suggests temporal disaggregation"
            else:
                method = "scaling"
                confidence = 0.85
                reason = "Low bias with good correlation - scaling sufficient"
            cluster_id = None

        # Estimate expected improvement
        expected_improvement = {
            "bias_reduction_pct": abs(mean_bias) * 0.9,  # Expect 90% reduction
            "mae_reduction_pct": 50.0 if method == "benchmarking" else 30.0,
            "rmse_reduction_pct": 45.0 if method == "benchmarking" else 25.0,
        }

        rec = SubperiodRecommendation(
            start=start,
            end=end,
            recommended_method=method,
            confidence=confidence,
            reason=reason,
            expected_improvement=expected_improvement,
            cluster_id=cluster_id,
        )
        recommendations.append(rec)

    # Sort by confidence
    recommendations.sort(key=lambda x: x.confidence, reverse=True)

    return recommendations


def detect_bias_patterns(
    indicator: pd.Series,
    target: pd.Series,
    variable: str,
    window_size: str = "30D",
    step_size: str = "7D",
    n_clusters: int = 3,
    changepoint_method: Literal["pelt", "binary_segmentation", "threshold"] = "threshold",
    changepoint_threshold: float = 5.0,
) -> BiasDetectionResult:
    """
    Comprehensive bias pattern detection and analysis.

    Parameters
    ----------
    indicator : pd.Series
        High-frequency indicator series
    target : pd.Series
        Low-frequency target series
    variable : str
        Variable name (e.g., 'river', 'solar')
    window_size : str
        Rolling window size
    step_size : str
        Step between windows
    n_clusters : int
        Number of clusters for period grouping
    changepoint_method : str
        Method for changepoint detection
    changepoint_threshold : float
        Threshold for changepoint detection

    Returns
    -------
    BiasDetectionResult
        Complete analysis results
    """
    # Overall comparison - resample indicator to daily first for proper comparison
    indicator_daily = indicator.resample("D").sum()
    overall = compare_series(indicator_daily, target)
    overall_bias = ((overall["mean_a"] / overall["mean_b"]) - 1.0) * 100.0

    # Rolling window analysis
    windows = rolling_bias_analysis(indicator, target, window_size=window_size, step_size=step_size)

    # Changepoint detection
    changepoints = detect_changepoints(
        windows, method=changepoint_method, threshold=changepoint_threshold
    )

    # Clustering
    clusters = cluster_periods(windows, n_clusters=n_clusters)

    # Generate recommendations
    recommendations = recommend_adjustment_strategy(windows, changepoints, clusters)

    result = BiasDetectionResult(
        variable=variable,
        overall_bias_pct=overall_bias,
        overall_mae=overall["mae"],
        overall_rmse=overall["rmse"],
        rolling_windows=windows,
        changepoints=changepoints,
        clusters=clusters,
        recommendations=recommendations,
        metadata={
            "window_size": window_size,
            "step_size": step_size,
            "n_clusters": n_clusters,
            "n_windows": len(windows),
        },
    )

    return result
