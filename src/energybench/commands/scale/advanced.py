from pathlib import Path
from energybench.io.input import read_csv
from energybench.variables import get_variable_config
from pandas import DataFrame, Timestamp
from energybench.models.scaling import advanced_daily_scaling
from energybench.io.output import save_dataframe, build_filename


def scale_high_frequency_series_advanced(
    variable: str,
    high_frequency_csv: Path,
    low_frequency_csv: Path,
    start: Timestamp,
    end: Timestamp,
    high_frequency_datetime_column: str = "DateTime",
    low_frequency_datetime_column: str = "Date",
    output_dir: Path = Path("output"),
    min_value: float = 0.0,
    preserve_zeros: bool = True,
    warn_threshold: float = 10.0,
    min_daily_sum: float = 0.01,
):
    """
    Advanced daily scaling with additional constraints.

    This method scales hourly values to match daily targets while:
    - Enforcing minimum values (default: 0.0)
    - Optionally preserving zero values in the original series
    - Redistributing remainders across non-zero hours when preserve_zeros=True

    Args:
        variable: Energy type (nuclear, water, river, storage, solar, wind, thermal)
        high_frequency_csv: Path to hourly indicator source data
        low_frequency_csv: Path to daily target source data
        start: Start timestamp
        end: End timestamp
        high_frequency_datetime_column: Column name for hourly timestamps
        low_frequency_datetime_column: Column name for daily timestamps
        output_dir: Directory for output files
        min_value: Minimum allowed value after scaling (default: 0.0)
        preserve_zeros: Keep zeros from original series (default: True)
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

    scaled_series = advanced_daily_scaling(
        high_frequency_series=high_frequency_series,
        low_frequency_series=low_frequency_series,
        min_value=min_value,
        preserve_zeros=preserve_zeros,
        warn_threshold=warn_threshold,
        min_daily_sum=min_daily_sum,
    )

    out = DataFrame(
        {
            "DateTime": scaled_series.index,
            cfg["original_column"]: high_frequency_series.reindex(scaled_series.index).values,
            cfg["scaled_per_day_values"][0]: scaled_series,
        }
    )
    out["high_frequency_set"] = "indicator source"
    out["high_frequency_type"] = ", ".join(cfg["indicator_type"])
    out["low_frequency_set"] = "target source"
    out["low_frequency_type"] = ", ".join(cfg["target_type"])
    out["scaling_method"] = "advanced_daily"
    out["min_value"] = min_value
    out["preserve_zeros"] = preserve_zeros

    filename = build_filename(
        base_name="hourly_scaled_advanced",
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
    print(f"   Settings: min_value={min_value}, preserve_zeros={preserve_zeros}")


if __name__ == "__main__":
    app()
