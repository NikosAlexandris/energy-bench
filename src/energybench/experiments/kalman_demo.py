from __future__ import annotations

from pathlib import Path
from energybench.helpers import sum_columns
from energybench.io.input import read_csv
import numpy as np
import pandas as pd
from pandas import Timestamp

from energybench.models.kalman_reconcile import (
    kalman_filter_1d,
    reconcile_to_daily_totals,
)
from energybench.validate.daily_check import build_daily_validation


from energybench.variables import get_variable_config


OUTPUT_DIR = Path("output")


def make_toy_data(
    start: str = "2026-01-01 00:00:00",
    days: int = 10,
    seed: int = 42,
) -> tuple[pd.Series, pd.Series, pd.Series]:
    rng = np.random.default_rng(seed)

    index = pd.date_range(start=start, periods=days * 24, freq="h")
    hour = index.hour.to_numpy()

    diurnal = 0.6 + 0.5 * np.sin((hour - 7) / 24 * 2 * np.pi) ** 2
    weekly = np.where(index.dayofweek.to_numpy() >= 5, 0.92, 1.0)

    true_hourly = 3.0 + 2.0 * diurnal * weekly + rng.normal(0, 0.10, len(index))
    true_hourly = np.clip(true_hourly, 0.05, None)

    indicator_hourly = true_hourly * 0.78 + rng.normal(0, 0.18, len(index))
    indicator_hourly = np.clip(indicator_hourly, 0.01, None)

    true_series = pd.Series(true_hourly, index=index, name="true_hourly_gwh")
    indicator_series = pd.Series(
        indicator_hourly, index=index, name="indicator_hourly_gwh"
    )
    daily_reference = true_series.resample("D").sum().rename("daily_reference_gwh")

    print(f"> Generated toy data...")

    return true_series, indicator_series, daily_reference


def main(
    indicator_hourly_csv: Path,
    daily_reference_csv: Path,
    start: Timestamp,
    end: Timestamp,
    high_frequency_datetime_column: str = "DateTime",
    low_frequency_datetime_column: str = "Date",
) -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    # true_hourly, indicator_hourly, daily_reference = make_toy_data()
    indicator_hourly = read_csv(
        source=indicator_hourly_csv,
        start=start,
        end=end,
        time_column=high_frequency_datetime_column,
    )

    daily_reference = read_csv(
        source=daily_reference_csv,
        start=start.normalize(),
        end=end.normalize(),
        time_column=low_frequency_datetime_column,
    )

    filtered_hourly = kalman_filter_1d(
        observations=indicator_hourly,
        process_variance=0.03,
        observation_variance=0.12,
    )

    reconciled_hourly = reconcile_to_daily_totals(
        hourly_series=filtered_hourly,
        daily_reference=daily_reference,
    )

    validation = build_daily_validation(
        original_hourly=indicator_hourly,
        filtered_hourly=filtered_hourly,
        reconciled_hourly=reconciled_hourly,
        daily_reference=daily_reference,
    )

    hourly_out = pd.concat(
        # [true_hourly, indicator_hourly, filtered_hourly, reconciled_hourly],
        [indicator_hourly, filtered_hourly, reconciled_hourly],
        axis=1,
    )
    hourly_out.to_csv(OUTPUT_DIR / "kalman_toy_hourly.csv", index=True)
    validation.to_csv(OUTPUT_DIR / "kalman_toy_validation.csv", index=True)

    print(f"> Wrote {OUTPUT_DIR / 'kalman_toy_hourly.csv'}")
    print(f"> Wrote {OUTPUT_DIR / 'kalman_toy_validation.csv'}")


def kalman_benchmark(
    variable: str,
    high_frequency_csv: Path,
    low_frequency_csv: Path,
    start: Timestamp,
    end: Timestamp,
    high_frequency_datetime_column: str = "DateTime",
    low_frequency_datetime_column: str = "Date",
    process_variance: float = 0.03,
    observation_variance: float = 0.12,
    output_dir: Path = OUTPUT_DIR,
) -> tuple[Path, Path]:
    """
    """
    cfg = get_variable_config(variable)
    output_dir.mkdir(parents=True, exist_ok=True)

    high_frequency_df = read_csv(
        source=high_frequency_csv,
        start=start,
        end=end,
        time_column=high_frequency_datetime_column,
    )

    low_frequency_df = read_csv(
        source=low_frequency_csv,
        start=start.normalize(),
        end=end.normalize(),
        time_column=low_frequency_datetime_column,
    )

    high_frequency = sum_columns(
        high_frequency_df,
        cfg["indicator_columns"],
        f"{variable}_high_frequency_original_gwh",
    )

    low_frequency = sum_columns(
        low_frequency_df,
        cfg["target_columns"],
        f"{variable}_low_frequency_gwh",
    )

    # filtered_hourly = kalman_filter_1d(
    #     observations=high_frequency,
    #     process_variance=process_variance,
    #     observation_variance=observation_variance,
    # )
    # filtered_hourly = kalman_filter_1d(
    #     observations=high_frequency,
    #     process_variance=process_variance,
    #     observation_variance=observation_variance,
    # ).rename(f"{variable}_kalman_filtered_gwh")
    filtered_hourly = kalman_filter_1d(
        observations=high_frequency,
        process_variance=process_variance,
        observation_variance=observation_variance,
    ).rename(f"{variable}_kalman_filtered_gwh")

    # reconciled_hourly = reconcile_to_daily_totals(
    #     hourly_series=filtered_hourly,
    #     daily_reference=low_frequency,
    # )
    # reconciled_hourly = reconcile_to_daily_totals(
    #     hourly_series=filtered_hourly,
    #     daily_reference=low_frequency,
    # ).rename(f"{variable}_hourly_reconciled_gwh")
    reconciled_hourly = reconcile_to_daily_totals(
        hourly_series=filtered_hourly,
        daily_reference=low_frequency,
    ).rename(cfg["output_column"])




    validation = build_daily_validation(
        original_hourly=high_frequency,
        filtered_hourly=filtered_hourly,
        reconciled_hourly=reconciled_hourly,
        daily_reference=low_frequency,
    )

    hourly_out = pd.concat(
        [high_frequency, filtered_hourly, reconciled_hourly],
        axis=1,
    )

    hourly_path = output_dir / f"kalman_{variable}_hourly.csv"
    validation_path = output_dir / f"kalman_{variable}_validation.csv"

    hourly_out.to_csv(hourly_path, index=True)
    validation.to_csv(validation_path, index=True)

    return hourly_path, validation_path


if __name__ == "__main__":
    main()
