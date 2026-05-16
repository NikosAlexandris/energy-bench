from pathlib import Path
from energybench.helpers import sum_columns
import pandas as pd
from pandas import Timestamp
from energybench.plots.difference import plot_series_difference
from energybench.variables import get_variable_config
from energybench.io.output import save_figure, build_filename


def plot_original_vs_target(
    original_high_frequency_csv: Path,
    target_low_frequency_csv: Path,
    variable: str,
    start: pd.Timestamp,
    end: Timestamp,
    target_data_source: str = "Low-frequency source",
    original_data_source: str = "High-frequency source",
    original_datetime_column: str = "DateTime",
    target_datetime_column: str = "Date",
    original_series_label: str | None = "High-frequency original series",
    target_series_label: str | None = "Low-frequency target series",
    xlabel: str = "Time",
    units: str = "GWh",
    # ylabel: str = "GWh",
    output_directory: Path = Path("output"),
    output_filename: Path = Path("original_vs_target.png"),
):
    """
    Plot original high-frequency series (aggregates) against low-frequency
    target series.  Shows eventually why adjustment is needed (original ≠
    target).

    Parameters
    ----------
    high_frequency_csv : Path
        high_frequency_csv
    low_frequency_csv : Path
        low_frequency_csv
    variable : str
        variable
    start : pd.Timestamp
        start
    end : Timestamp
        end
    target_data_source : str
        target_data_source
    original_data_source : str
        original_data_source
    high_frequency_datetime_column : str
        high_frequency_datetime_column
    low_frequency_datetime_column : str
        low_frequency_datetime_column
    original_series_label : str | None
        original_series_label
    target_series_label : str | None
        target_series_label
    xlabel : str
        xlabel
    units : str
        units
    output_directory : Path
        output_directory
    output_filename : Path
        Filename under which to save the plot. Default suffix is `.png` and
        prefix is the user-requested `variable`.

    """
    cfg = get_variable_config(variable)

    # Original: high-frequency aggregated to daily
    high_frequency_dataframe = pd.read_csv(
        original_high_frequency_csv, parse_dates=[original_datetime_column]
    ).set_index(original_datetime_column)

    # Daily aggregation of indicator columns
    cfg = get_variable_config(variable, high_frequency_types=high_frequency_dataframe.columns)
    original_daily = (
        sum_columns(
            df=high_frequency_dataframe.loc[start:end],
            columns=cfg["entsoe_types"],
            output_name=f"{cfg['key']}_original_daily",
        )
        .resample("D")
        .sum()
    )

    # Target: low-frequency reference
    low_freq = pd.read_csv(
        target_low_frequency_csv,
        parse_dates=[target_datetime_column],
        index_col=target_datetime_column,
    )
    low_freq = low_freq.loc[start.normalize() : end.normalize()]
    target_daily = low_freq[cfg["sfoe_types"]].sum(axis=1)

    # Align indexes
    common_idx = original_daily.index.union(target_daily.index).sort_values()
    original_daily = original_daily.reindex(common_idx)
    target_daily = target_daily.reindex(common_idx)

    figure = plot_series_difference(
        target_series=target_daily,
        benchmarked_series=original_daily,  # Reuses "benchmarked" parameter for original
        target_data_source=target_data_source,
        benchmarked_data_source=original_data_source,
        electricity_generation_type=f"{cfg['label']}",
        frequency="daily",
        target_series_label=target_series_label,  # or f"{data_source}",
        benchmarked_series_label=original_series_label,
        units=units,
        xlabel=xlabel,
        # output_directory=output_directory,
    )

    filename = build_filename(
        base_name=output_filename.stem,
        variable=variable,
        start=start,
        end=end,
        suffix=".png",
    )

    save_figure(
        fig=figure,
        filename=filename,
        output_dir=output_directory,
        variable=variable,
        close_after=False,
    )
