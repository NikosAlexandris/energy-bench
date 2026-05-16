from __future__ import annotations
from pathlib import Path
from energybench.validate.build import KindOfCSV
import pandas as pd
import numpy as np
from pandas import Timestamp
from energybench.variables import get_variable_config
from energybench.print.metrics import print_metrics
from energybench.io.input import read_csv
from energybench.io.output import save_dataframe


def compare_scaled_vs_target(
    scaled_csv: Path,
    target_csv: Path,
    variable: str,
    start: Timestamp,
    end: Timestamp,
    kind_of_csv: KindOfCSV = KindOfCSV.scaled,
    output_csv: Path | None = None,
    scaled_datetime_column: str = "DateTime",
    target_date_column: str = "Date",
    scaled_column: str | None = None,
    category_name: str | None = None,
):
    """
    Compare scaled hourly series (aggregated to daily) vs daily target targets.
    This validates that the scaling correctly matched the target daily totals.
    """
    cfg = get_variable_config(variable)

    kind_of_value_column = {
        "benchmarked": cfg["benchmarked_values"],
        "scaled": cfg["scaled_values"],
        "scaled-per-day": cfg["scaled_per_day_values"],
    }

    if kind_of_csv not in kind_of_value_column:
        raise ValueError(
            f"Unknown result_kind={kind_of_csv!r}. "
            f"Expected one of: {', '.join(kind_of_value_column)}"
        )

    # Read scaled hourly data
    scaled_df = pd.read_csv(
        scaled_csv,
        parse_dates=[scaled_datetime_column],
    ).set_index(scaled_datetime_column)
    scaled_df = scaled_df.loc[start:end]

    # Extract scaled series and aggregate to daily
    if not scaled_column:
        scaled_column = kind_of_value_column[kind_of_csv.value][0]
    scaled_hourly = scaled_df[scaled_column].loc[start:end].sort_index()
    scaled_daily = scaled_hourly.resample("D").sum()

    # Read daily target targets
    target_df = read_csv(
        source=target_csv,
        start=start.normalize(),
        end=end.normalize(),
        time_column=target_date_column,
        columns=[target_date_column] + cfg["target_types_present"],
    )
    from energybench.helpers import sum_columns

    target_daily = sum_columns(target_df, cfg["target_types_present"], "target")

    # Compare daily totals
    daily_metrics = compare_series(scaled_daily, target_daily)

    # Build output row with proper category name
    if category_name is None:
        category_name = f"{variable}_{kind_of_csv.name}_vs_target"

    row = {
        "category": category_name,
        "label_daily": f"{category_name} daily validation",
        "label_shape": "N/A (daily comparison only)",
        "start": pd.Timestamp(start),
        "end": pd.Timestamp(end),
        **daily_metrics.to_dict(),
        "n_days": len(scaled_daily),
        "mean_daily_shape_corr": np.nan,
        "median_daily_shape_corr": np.nan,
        "mean_daily_shape_mae": np.nan,
        "median_daily_shape_mae": np.nan,
    }

    # Calculate bias percentage
    if "mean_a" in row and "mean_b" in row and row["mean_b"] not in (0, None):
        row["bias_pct"] = (row["mean_a"] / row["mean_b"] - 1.0) * 100.0
    else:
        row["bias_pct"] = float("nan")

    # Print results
    print_metrics(row["label_daily"], daily_metrics)
    print(f"\n📊 Validation Summary:")
    print(f"   Scaled daily sum: {row['sum_a']:.2f} GWh")
    print(f"   Target daily sum: {row['sum_b']:.2f} GWh")
    print(f"   Bias: {row['bias_pct']:.2f}%")
    print(f"   MAE: {row['mae']:.4f} GWh")
    print(f"   Pearson correlation: {row['pearson']:.4f}")

    # Export to CSV if requested
    if output_csv is not None:
        out = pd.DataFrame([row])

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
            "best_lag_corr",
            "bias_pct",
            "n_days",
            "mean_daily_shape_corr",
            "median_daily_shape_corr",
            "mean_daily_shape_mae",
            "median_daily_shape_mae",
            "label_daily",
            "label_shape",
        ]
        cols = [c for c in preferred_order if c in out.columns] + [
            c for c in out.columns if c not in preferred_order
        ]
        out = out[cols]

        save_dataframe(
            df=out,
            filename=output_csv,
            output_dir=output_csv.parent if output_csv.is_absolute() else Path("output"),
            variable=variable,
            index=False,
        )
    else:
        print(pd.DataFrame([row]).to_string(index=False))
