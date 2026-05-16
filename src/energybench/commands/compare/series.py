from __future__ import annotations
from pathlib import Path
from pandas import Timestamp, DataFrame
from energybench.compare.specifications import COMPARISON_SPECS
from energybench.compare.shape import compare_intraday_shape, compute_comparison_row
from energybench.helpers import sum_columns
from energybench.io.reading import read_csv
from energybench.print.metrics import print_metrics
from energybench.io.writing import save_dataframe


def compare_series_shape(
    high_frequency_csv: Path,
    low_frequency_csv: Path,
    start: Timestamp,
    end: Timestamp,
    output_csv: Path | None = None,
    high_frequency_datetime_column: str = "DateTime",
    low_frequency_date_column: str = "Date",
    self_test: bool = False,
):
    """
    Compare hourly indicator series against daily target series expanded to flat hourly.
    Optionally export all metrics to a tidy CSV for later plotting.
    """
    indicator_data = read_csv(
        high_frequency_csv,
        start=start,
        end=end,
        time_column=high_frequency_datetime_column,
    )
    target_data = read_csv(
        low_frequency_csv,
        start=start,
        end=end,
        time_column=low_frequency_date_column,
    )

    if self_test:
        hydro_hourly = sum_columns(
            indicator_data,
            [
                "Hydro Run-of-river and poundage",
                "Hydro Water Reservoir",
                "Hydro Pumped Storage",
            ],
            label="hydro_hourly",
        ).loc[start:end]
        print_metrics("Self-Test", compare_intraday_shape(hydro_hourly, hydro_hourly))
        return

    rows = []

    for spec in COMPARISON_SPECS:
        daily_metrics, shape_metrics, row = compute_comparison_row(
            indicator_data=indicator_data,
            target_data=target_data,
            spec=spec,
            start=start,
            end=end,
        )

        print_metrics(spec["label_daily"], daily_metrics)
        print_metrics(spec["label_shape"], shape_metrics)
        rows.append(row)

    if output_csv is not None:
        out = DataFrame(rows)

        preferred_order = [
            "category",
            "start",
            "end",
            "n_overlap",
            "pearson",
            "spearman",
            "cosine",
            "mbe",
            "mae",
            "rmse",
            "nrmse_mean",
            "smape",
            "mean_a",
            "mean_b",
            "std_a",
            "std_b",
            "sum_a",
            "sum_b",
            "best_lag",
            "bias_pct",
            "n_days",
            "mean_daily_shape_corr",
            "median_daily_shape_corr",
            "mean_daily_shape_mae",
            "median_daily_shape_mae",
        ]
        cols = [c for c in preferred_order if c in out.columns] + [
            c for c in out.columns if c not in preferred_order
        ]
        out = out[cols]

        if output_csv:
            save_dataframe(
                df=out,
                filename=output_csv,
                output_dir=output_csv.parent if output_csv.is_absolute() else Path("output"),
                variable=None,  # No variable subdirectory for comparison metrics
                index=False,
            )
        else:
            print(out.to_string(index=False))
