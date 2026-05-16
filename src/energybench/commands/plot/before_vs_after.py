from pathlib import Path
import pandas as pd
from pandas import Timestamp
from energybench.plots.before_after import plot_series_before_and_after
from energybench.validate.build import KindOfCSV
from energybench.variables import get_variable_config
from energybench.io.output import save_figure, build_filename


def plot_before_vs_after(
    after_csv: Path,
    variable: str,
    start: Timestamp,
    end: Timestamp,
    kind_of_csv: KindOfCSV = KindOfCSV.scaled,
    indicator_series_label: str | None = None,
    after_series_label: str | None = None,
    data_source: str | None = None,  #"High-frequency series",
    reconstruction_method: str | None = None,
    datetime_column: str = "DateTime",
    output_directory: Path = Path("output"),
    output_filename: Path = Path("before_vs_after.png"),
):
    """
    Plot the indicator (before) vs the benchmarked (after) high-frequency time
    series side by side.
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

    # df = pd.read_csv(benchmark_csv, parse_dates=[datetime_column]).set_index(datetime_column)
    df = pd.read_csv(
        after_csv,
        parse_dates=[datetime_column],
    ).set_index(datetime_column)
    df = df.loc[start:end]

    figure = plot_series_before_and_after(
        dataframe=df,
        original_series=cfg["original_column"],
        adjusted_series=kind_of_value_column[kind_of_csv.value][0],
        original_series_label=indicator_series_label,
        adjusted_series_label=after_series_label,
        data_source=data_source,
        reconstruction_method=reconstruction_method,
        electricity_generation_type=cfg["label"],
        frequency="hourly",
        # units=units,
    )

    filename = build_filename(
        base_name=f"{output_filename.stem}_{kind_of_csv.name}",
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
