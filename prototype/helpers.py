import pandas as pd
import numpy as np


def prepare_dataframe(
    low_frequency_target: pd.Series,
    high_frequency_indicator: pd.Series,
) -> pd.DataFrame:
    """
    Convert low-frequency target series and high-frequency indicator series to
    a `tempdisagg` compatible input format.
    """
    low_frequency_target = low_frequency_target.copy()
    high_frequency_indicator = high_frequency_indicator.copy()

    # Ensure time series feature a DatetimeIndex
    if not isinstance(low_frequency_target.index, pd.DatetimeIndex):
        low_frequency_target.index = pd.to_datetime(low_frequency_target.index)

    if not isinstance(high_frequency_indicator.index, pd.DatetimeIndex):
        high_frequency_indicator.index = pd.to_datetime(high_frequency_indicator.index)

    dates = low_frequency_target.index.normalize().date
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
        d.year * 10000 + d.month * 100 + d.day: v
        for d, v in zip(dates, low_frequency_target.values)
    }
    df["y"] = df["Index"].map(daily_map)

    # High-freq indicator X
    high_resampled = high_frequency_indicator.reindex(
        hourly_index,
        method="nearest"
    ).ffill().bfill()
    df["X"] = high_resampled.values

    return df
