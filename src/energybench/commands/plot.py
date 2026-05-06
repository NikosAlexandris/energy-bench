from pathlib import Path
import pandas as pd
# from energybench.read import read_csv
from cyclopts import App
from pandas import Timestamp
from energybench.plots.before_after import plot_series_before_and_after
from energybench.plots.difference import plot_series_difference
from energybench.validate.build import build_validation_table
from energybench.variables import get_variable_config


app = App(help="Plot utilities for benchmarked outputs.")


@app.command(name='before-after')
def before_after(
    benchmark_csv: Path,
    variable: str,
    indicator_series_label: str | None = None,
    benchmarked_series_label: str | None = None,
    data_source: str | None = None,  #"High-frequency series",
    datetime_column: str = "DateTime",
    output_dir: Path = Path("output"),
):
    """
    Plot the indicator (before) vs the benchmarked (after) high-frequency time
    series side by side.
    """
    cfg = get_variable_config(variable)
    # df = pd.read_csv(benchmark_csv, parse_dates=[datetime_column]).set_index(datetime_column)
    df = pd.read_csv(benchmark_csv, parse_dates=[datetime_column]).set_index(datetime_column)
    plot_series_before_and_after(
        dataframe=df,
        original_series=cfg["original_column"],
        adjusted_series=cfg["output_column"],
        original_series_label=indicator_series_label,
        adjusted_series_label=benchmarked_series_label,
        data_source=data_source,
        electricity_generation_type=cfg["label"],
        frequency="hourly",
        output_directory=output_dir,
    )


@app.command(name="difference")
def difference(
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
):
    """
    Plot benchmarked vs target series and their difference.
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
        electricity_generation_type=cfg["label"],  #electricity_generation_type,
        frequency="Daily",  #frequency.lower(),  # FixMe : needed here is the frequency written out !
        benchmarked_series_label=benchmarked_series_label or f"{high_frequency_data_source}",
        target_series_label=target_series_label or f"{low_frequency_data_source}",
        #
        units=units,  # ylabel,
        xlabel=xlabel,
        output_directory=output_directory,
    )


@app.command(name="original-vs-target")
def original_vs_target(
    high_frequency_csv: Path,
    low_frequency_csv: Path,
    variable: str,
    start: pd.Timestamp,
    end: Timestamp,
    target_data_source: str = "Low-frequency source",
    original_data_source: str = "High-frequency source",
    high_frequency_datetime_column: str = "DateTime",
    low_frequency_datetime_column: str = "Date",
    original_series_label: str | None = "High-frequency indicator series",
    target_series_label: str | None = "Low-frequency target series",
    xlabel: str = "Time",
    units: str = "GWh",
    # ylabel: str = "GWh",
    output_directory: Path = Path("output"),
):
    """
    Plot original high-frequency aggregates vs low-frequency target.
    
    Shows why benchmarking was needed (original ≠ target).
    """
    cfg = get_variable_config(variable)

    # Original: high-frequency aggregated to daily
    high_freq = pd.read_csv(
        high_frequency_csv, 
        parse_dates=[high_frequency_datetime_column]
    ).set_index(high_frequency_datetime_column)
    original_daily = (
        high_freq[cfg["high_frequency_value_columns"]]
        .sum(axis=1)
        .loc[start:end]
        .resample("D").sum()
    )

    # Target: low-frequency reference
    low_freq = pd.read_csv(
        low_frequency_csv, 
        parse_dates=[low_frequency_datetime_column], 
        index_col=low_frequency_datetime_column
    )
    low_freq = low_freq.loc[start.normalize():end.normalize()]
    target_daily = low_freq[cfg["low_frequency_columns"]].sum(axis=1)

    # Align indexes
    common_idx = original_daily.index.union(target_daily.index).sort_values()
    original_daily = original_daily.reindex(common_idx)
    target_daily = target_daily.reindex(common_idx)

    plot_series_difference(
        target_series=target_daily,
        benchmarked_series=original_daily,  # Reuses "benchmarked" parameter for original
        target_data_source=target_data_source,
        benchmarked_data_source=original_data_source,
        electricity_generation_type=f"{cfg['label']}",
        frequency="daily",
        target_series_label=target_series_label,  #or f"{data_source}",
        benchmarked_series_label=original_series_label,
        units=units,
        xlabel=xlabel,
        output_filename=Path(f"{variable}_original_vs_target"),
        output_directory=output_directory,
    )


if __name__ == "__main__":
    app()
