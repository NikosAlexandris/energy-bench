import numpy as np
import pandas as pd


def scale_series(
    indicator_series: pd.Series,
    target_series: pd.Series,
    warn_threshold: float = 10.0,
    min_daily_sum: float = 0.01,
) -> pd.Series:
    """
    Scale high-frequency indicator series to match low-frequency targets.

    Args:
        indicator_series: High-frequency data to scale (e.g., hourly)
        target_series: Low-frequency targets (e.g., daily)
        warn_threshold: Warn if scaling factor exceeds this value (default: 10.0)
        min_daily_sum: Skip scaling if daily sum is below this threshold (default: 0.01 GWh)

    Returns:
        Scaled series with warnings for extreme factors
    """
    indicator_series = indicator_series.sort_index().astype(float)
    target_series = target_series.sort_index().astype(float)

    day_index = indicator_series.index.normalize()
    daily_sum = indicator_series.groupby(day_index).sum()

    factor = target_series.reindex(daily_sum.index) / daily_sum
    factor = factor.replace([np.inf, -np.inf], np.nan)

    # Detect extreme scaling factors
    extreme_factors = factor[factor.abs() > warn_threshold].dropna()
    if len(extreme_factors) > 0:
        print(
            f"⚠️  Warning: {len(extreme_factors)} days have extreme scaling factors (>{warn_threshold}x):"
        )
        for day, f in extreme_factors.head(5).items():
            daily_val = daily_sum.loc[day]
            target_val = target_series.loc[day]
            print(
                f"   {pd.Timestamp(day).date()}: factor={f:.1f}x (daily_sum={daily_val:.4f} GWh, target={target_val:.2f} GWh)"
            )
        if len(extreme_factors) > 5:
            print(f"   ... and {len(extreme_factors) - 5} more days")

    # Detect very small daily sums that might cause issues
    small_sums = daily_sum[(daily_sum > 0) & (daily_sum < min_daily_sum)]
    if len(small_sums) > 0:
        print(
            f"⚠️  Warning: {len(small_sums)} days have very small hourly sums (<{min_daily_sum} GWh):"
        )
        for day, s in small_sums.head(5).items():
            print(f"   {pd.Timestamp(day).date()}: sum={s:.6f} GWh")
        if len(small_sums) > 5:
            print(f"   ... and {len(small_sums) - 5} more days")
        print(
            "   Consider using the --min-value parameter or checking data quality."
        )

    scaled_series = indicator_series * factor.reindex(day_index).to_numpy()

    # Keep original values where factor is missing
    missing_days = factor.reindex(day_index).isna().to_numpy()
    scaled_series = scaled_series.where(~missing_days, indicator_series)

    return scaled_series


def advanced_daily_scaling(
    indicator_series: pd.Series,
    target_series: pd.Series,
    min_value: float = 0.0,
    preserve_zeros: bool = True,
    warn_threshold: float = 10.0,
    min_daily_sum: float = 0.01,
) -> pd.Series:
    """
    Advanced daily scaling with constraints and validation.

    Args:
        indicator_series: High-frequency data to scale (e.g., hourly)
        target_series: Low-frequency targets (e.g., daily)
        min_value: Minimum allowed value after scaling (default: 0.0)
        preserve_zeros: Keep zeros from original series (default: True)
        warn_threshold: Warn if scaling factor exceeds this value (default: 10.0)
        min_daily_sum: Skip scaling if daily sum is below this threshold (default: 0.01 GWh)

    Returns:
        Scaled series with constraints applied
    """
    indicator_series = indicator_series.sort_index().astype(float)
    target_series = target_series.sort_index().astype(float)

    out = []
    extreme_days = []
    small_sum_days = []

    for day, x in indicator_series.groupby(indicator_series.index.normalize()):
        # Try to get target value for this day
        try:
            target = target_series.loc[pd.Timestamp(day)]
        except KeyError:
            target = np.nan

        if pd.isna(target):
            out.append(x)
            continue

        x = x.copy()

        # Create zero mask BEFORE clipping (to preserve original zeros)
        if preserve_zeros:
            mask = x == 0
        else:
            mask = pd.Series(False, index=x.index)

        # Now clip values to minimum
        x = x.clip(lower=min_value)

        s = x.sum(skipna=True)

        # Check for very small sums that might cause extreme scaling
        if 0 < s < min_daily_sum:
            small_sum_days.append((day, s, target))
            # Use original values for days with very small sums
            out.append(x)
            continue

        if s > 0 and not np.isnan(s):
            factor = target / s
            # Check for extreme scaling factors
            if abs(factor) > warn_threshold:
                extreme_days.append((day, factor, s, target))
            y = x * factor
        else:
            # If sum is zero or NaN, distribute evenly
            n = len(x)
            y = pd.Series(target / n, index=x.index)

        if preserve_zeros:
            # Set originally-zero values back to zero
            y[mask] = 0.0
            # Redistribute the remainder across non-zero hours
            rem = target - y.sum()
            if rem != 0 and (~mask).any():
                y.loc[~mask] += rem / (~mask).sum()

        out.append(y)

    # Report warnings
    if extreme_days:
        print(
            f"⚠️  Warning: {len(extreme_days)} days have extreme scaling factors (>{warn_threshold}x):"
        )
        for day, factor, daily_sum, target in extreme_days[:5]:
            print(
                f"   {day.date()}: factor={factor:.1f}x (daily_sum={daily_sum:.4f} GWh, target={target:.2f} GWh)"
            )
        if len(extreme_days) > 5:
            print(f"   ... and {len(extreme_days) - 5} more days")

    if small_sum_days:
        print(
            f"⚠️  Warning: {len(small_sum_days)} days have very small hourly sums (<{min_daily_sum} GWh):"
        )
        print(f"   These days were NOT scaled to avoid extreme values.")
        for day, s, target in small_sum_days[:5]:
            print(f"   {day.date()}: sum={s:.6f} GWh (target={target:.2f} GWh)")
        if len(small_sum_days) > 5:
            print(f"   ... and {len(small_sum_days) - 5} more days")
        print(f"   Consider checking data quality or adjusting min_daily_sum parameter.")

    return pd.concat(out).sort_index()
