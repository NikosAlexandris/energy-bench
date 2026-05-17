from pathlib import Path
import pandas as pd
from plots.difference import plot_series_difference


def plot_validation_table(
    check: pd.DataFrame,
    data_source: str,
    electricity_generation_type: str,
    frequency: str = "daily",
    label: str = "daily target target",
    units: str = "GWh",
    xlabel: str = "Date",
    output_directory: Path = Path("output"),
) -> None:

    plot_series_difference(
        target_series=check["target"],
        benchmarked_series=check["benchmarked"],
        data_source=data_source,
        electricity_generation_type=electricity_generation_type,
        frequency=frequency,
        target_series_label=label,
        units=units,
        xlabel=xlabel,
        output_directory=output_directory,
    )
