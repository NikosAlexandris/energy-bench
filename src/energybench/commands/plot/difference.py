from pathlib import Path
from pandas import Timestamp
from energybench.plots.difference import plot_series_difference
from energybench.validate.build import build_validation_table
from energybench.variables import get_variable_config
from energybench.io.output import save_figure, build_filename


def plot_difference(
    benchmark_csv: Path,
    high_frequency_csv: Path,
    low_frequency_csv: Path,
    variable: str,
    start: Timestamp,
    end: Timestamp,
    benchmarked_series_label: str | None = None,
    target_series_label: str | None = None,
    high_frequency_data_source: str = "High-frequency series",
    low_frequency_data_source: str = "Low-frequency series",
    benchmark_datetime_column: str = "DateTime",
    high_frequency_datetime_column: str = "DateTime",
    low_frequency_datetime_column: str = "Date",
    frequency: str = "D",
    units: str = "GWh",
    # ylabel: str = "GWh",
    xlabel: str = "Time",
    output_directory: Path = Path("output"),
    output_filename: Path = Path("difference"),
):
    """
    Plot benchmarked vs target series and their difference.

    Parameters
    ----------
    benchmark_csv : Path
        benchmark_csv
    high_frequency_csv : Path
        high_frequency_csv
    low_frequency_csv : Path
        low_frequency_csv
    variable : str
        variable
    start : Timestamp
        start
    end : Timestamp
        end
    benchmarked_series_label : str | None
        benchmarked_series_label
    target_series_label : str | None
        target_series_label
    high_frequency_data_source : str
        high_frequency_data_source
    low_frequency_data_source : str
        low_frequency_data_source
    benchmark_datetime_column : str
        benchmark_datetime_column
    high_frequency_datetime_column : str
        high_frequency_datetime_column
    low_frequency_datetime_column : str
        low_frequency_datetime_column
    frequency : str
        frequency
    units : str
        units
    xlabel : str
        xlabel
    output_directory : Path
        output_directory
    output_filename : Path
        Filename under which to save the plot. Default suffix is `.png` and
        prefix is the user-requested `variable`.

    """
    cfg = get_variable_config(variable)
    check = build_validation_table(
        benchmark_csv=benchmark_csv,
        high_frequency_csv=high_frequency_csv,
        low_frequency_csv=low_frequency_csv,
        start=start,
        end=end,
        benchmark_value_columns=cfg["benchmark_value_columns"],
        high_frequency_value_columns=cfg["high_frequency_value_columns"],
        low_frequency_columns=cfg["low_frequency_columns"],
        benchmark_datetime_column=benchmark_datetime_column,
        high_frequency_datetime_column=high_frequency_datetime_column,
        low_frequency_date_column=low_frequency_datetime_column,
        frequency=frequency,
    )

    plot_series_difference(
        benchmarked_series=check["benchmarked"],
        target_series=check["target"],
        #
        benchmarked_data_source=high_frequency_data_source,
        target_data_source=low_frequency_data_source,
        #
        electricity_generation_type=cfg["label"],  # electricity_generation_type,
        frequency="Daily",  # frequency.lower(),  # FixMe : needed here is the frequency written out !
        benchmarked_series_label=benchmarked_series_label or f"{high_frequency_data_source}",
        target_series_label=target_series_label or f"{low_frequency_data_source}",
        #
        units=units,  # ylabel,
        xlabel=xlabel,
    )

    if output_filename is None:
        filename = build_filename(
            base_name=f"difference_{frequency}",
            variable=variable,
            start=start,
            end=end,
            suffix=".png",
        )
    else:
        filename = output_filename.with_suffix(".png")

    save_figure(
        filename=filename,
        output_dir=output_directory,
        variable=variable if output_filename is None else None,
        close_after=True,
    )
