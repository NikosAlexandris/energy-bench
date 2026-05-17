import pandas as pd
import numpy as np
import warnings


def sum_columns(
    df: pd.DataFrame,
    columns: list[str],
    output_name: str,
    factor: float = 1.0,
    strict: bool = False,
) -> pd.Series:
    """
    Sum specified columns, handling missing columns gracefully.

    This function sums the specified columns from a DataFrame, automatically
    handling missing columns based on the strict parameter. It's designed to
    work with any time series data sources.

    Parameters
    ----------
    df : pd.DataFrame
        Input DataFrame containing the columns to sum.
    columns : list of str
        List of column names to sum.
    output_name : str
        Name for the output Series.
    factor : float, default=1.0
        Multiplicative factor applied to the sum (e.g., for unit conversion).
    strict : bool, default=False
        If True, raises ValueError when any columns are missing.
        If False, warns about missing columns and continues with available ones.

    Returns
    -------
    pd.Series
        Series with summed values, named according to output_name.

    Raises
    ------
    ValueError
        If no columns are found, or if strict=True and any columns are missing.

    Examples
    --------
    Sum indicator columns:

    >>> indicator = sum_columns(
    ...     df=indicator_data,
    ...     columns=["Nuclear", "Hydro Run-of-river"],
    ...     output_name="total_generation"
    ... )

    Sum with unit conversion (MW to GWh):

    >>> target = sum_columns(
    ...     df=target_data,
    ...     columns=["Kernkraft", "Flusskraft"],
    ...     output_name="daily_total",
    ...     factor=0.001
    ... )

    Strict mode - raise error if columns missing:

    >>> result = sum_columns(
    ...     df=data,
    ...     columns=["Required1", "Required2"],
    ...     output_name="result",
    ...     strict=True
    ... )
    """
    available = [c for c in columns if c in df.columns]
    missing = [c for c in columns if c not in df.columns]

    if not available:
        raise ValueError(
            f"No columns found for '{output_name}'. "
            f"Expected columns: {columns}, "
            f"Available in DataFrame: {list(df.columns)}"
        )

    if missing:
        if strict:
            raise ValueError(
                f"Missing required columns for '{output_name}': {missing}. "
                f"Available columns: {available}"
            )
        else:
            print(f"⚠️  Warning: missing columns for '{output_name}': {missing}")
            print(f"   Using available columns: {available}")

    # Convert to numeric and sum, handling non-numeric values gracefully
    out = df[available].apply(pd.to_numeric, errors="coerce").sum(axis=1) * factor
    out.name = output_name

    return out


def safe_sum_series(
    df: pd.DataFrame,
    value_columns: list[str],
    series_name: str,
) -> pd.Series:
    """
    DEPRECATED: Use sum_columns() instead.

    This function is deprecated and will be removed in v2.0.0.
    Use sum_columns() with the same parameters instead.

    Args:
        df: Input DataFrame
        value_columns: List of column names to sum
        series_name: Name for output Series

    Returns:
        pd.Series: Summed series

    Example:
        >>> # Old way (deprecated)
        >>> result = safe_sum_series(df, ["col1", "col2"], "total")

        >>> # New way (recommended)
        >>> result = sum_columns(df, ["col1", "col2"], "total")
    """
    warnings.warn(
        "safe_sum_series() is deprecated and will be removed in v2.0.0. "
        "Use sum_columns(df, columns, output_name) instead.",
        DeprecationWarning,
        stacklevel=2,
    )
    return sum_columns(
        df=df, columns=value_columns, output_name=series_name, factor=1.0, strict=False
    )


def prepare_dataframe(
    target_series: pd.Series,
    indicator_series: pd.Series,
) -> pd.DataFrame:
    """
    Convert target and indicator series to tempdisagg-compatible format.

    This function prepares time series data for temporal disaggregation by
    converting low-frequency target values and high-frequency indicator values
    into the format required by the tempdisagg library.

    The function is source-agnostic and works with any time series data:
    - Target: Low-frequency reference values (e.g., daily, weekly)
    - Indicator: High-frequency values to be adjusted (e.g., hourly, 15-min)

    Parameters
    ----------
    target_series : pd.Series
        Low-frequency reference series (e.g., daily totals).
        Index must be datetime-like at low frequency.
    indicator_series : pd.Series
        High-frequency indicator series (e.g., hourly data).
        Index must be datetime-like at high frequency.

    Returns
    -------
    pd.DataFrame
        DataFrame in tempdisagg format with columns:
        - Index : Date identifier (YYYYMMDD format)
        - Grain : Hour of day (1-24)
        - y : Target values (daily totals)
        - X : Indicator values (hourly)

    Examples
    --------
    Hourly indicator vs daily target:

    >>> df = prepare_dataframe(
    ...     target_series=daily_target,
    ...     indicator_series=hourly_indicator
    ... )

    15-minute indicator vs daily target:

    >>> df = prepare_dataframe(
    ...     target_series=daily_target,
    ...     indicator_series=indicator_15min
    ... )
    """
    target_series = target_series.copy()
    indicator_series = indicator_series.copy()

    # Ensure time series have DatetimeIndex
    if not isinstance(target_series.index, pd.DatetimeIndex):
        target_series.index = pd.to_datetime(target_series.index)

    if not isinstance(indicator_series.index, pd.DatetimeIndex):
        indicator_series.index = pd.to_datetime(indicator_series.index)

    dates = target_series.index.normalize().date
    hourly_index = pd.date_range(
        start=dates[0],
        end=dates[-1] + pd.Timedelta("23h"),
        freq="h",
    )

    df = pd.DataFrame(
        {
            "Index": hourly_index.year * 10000 + hourly_index.month * 100 + hourly_index.day,
            "Grain": hourly_index.hour + 1,
            "y": np.nan,
        }
    )

    # Set daily constraints as DAILY TOTALS (not divided by 24)
    daily_map = {
        d.year * 10000 + d.month * 100 + d.day: v for d, v in zip(dates, target_series.values)
    }
    df["y"] = df["Index"].map(daily_map)

    # Resample indicator to hourly frequency
    indicator_resampled = indicator_series.reindex(hourly_index, method="nearest").ffill().bfill()
    df["X"] = indicator_resampled.values

    return df
