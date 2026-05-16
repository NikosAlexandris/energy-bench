from pathlib import Path
from energybench.io.input import read_csv
from energybench.variables import get_variable_config
from pandas import DataFrame, Timestamp
from energybench.models.scaling import scale_series
from energybench.io.output import save_dataframe, build_filename


def scale_high_frequency_series(
    variable: str,
    high_frequency_csv: Path,
    low_frequency_csv: Path,
    start: Timestamp,
    end: Timestamp,
    high_frequency_datetime_column: str = "DateTime",
    low_frequency_datetime_column: str = "Date",
    output_dir: Path = Path("output"),
    warn_threshold: float = 10.0,
    min_daily_sum: float = 0.01,
):
    """
    Benchmark nuclear generation.

    Low-frequency target:      target source Kernkraft (daily)
    High-frequency indicator:  indicator source Nuclear (hourly)
    """
    cfg = get_variable_config(variable)
    output_dir.mkdir(parents=True, exist_ok=True)

    low_frequency_series = read_csv(
        source=low_frequency_csv,
        start=start.normalize(),
        end=end.normalize(),
        time_column=low_frequency_datetime_column,
        columns=[low_frequency_datetime_column] + cfg["target_types_present"],
    ).squeeze()

    high_frequency_series = read_csv(
        source=high_frequency_csv,
        start=start,
        end=end,
        time_column=high_frequency_datetime_column,
        columns=[high_frequency_datetime_column] + cfg["indicator_types_present"],
    ).squeeze()

    scaled_series = scale_series(
        high_frequency_series=high_frequency_series,
        low_frequency_series=low_frequency_series,
        warn_threshold=warn_threshold,
        min_daily_sum=min_daily_sum,
    )
    out = DataFrame(
        {
            "DateTime": scaled_series.index,
            cfg["original_column"]: high_frequency_series.reindex(scaled_series.index).values,
            cfg["scaled_output_column"]: scaled_series,
        }
    )
    # out["variable"] = cfg["label"]
    out["high_frequency_set"] = "indicator source"
    out["high_frequency_type"] = ", ".join(cfg["indicator_type"])
    out["low_frequency_set"] = "target source"
    out["low_frequency_type"] = ", ".join(cfg["target_type"])

    filename = build_filename(
        base_name="hourly_scaled",
        variable=variable,
        start=start,
        end=end,
        suffix=".csv",
    )

    save_dataframe(
        df=out,
        filename=filename,
        output_dir=output_dir,
        variable=variable,
        index=False,
    )
