from pathlib import Path
from energybench.plots.metrics import plot_metrics_overview
import pandas as pd
from energybench.io.output import save_figure


def plot_comparison_metrics(
    series_comparison_csv: Path,
    # metrics_csv: Path,
    # start: Timestamp,
    # end: Timestamp,
    # datetime_column: str = "DateTime",
    # title: str = "2016–2025",
    output_directory: Path = Path("output"),
    output_filename: Path = Path("adjustment_metrics.png"),
):
    """
    Plot summary metrics from a CSV produced by nrgbnc stats commands.
    """
    series_comparison_statistics = pd.read_csv(series_comparison_csv)
    # series_comparison_statistics = read_csv(
    #     source=series_comparison_csv,
    #     start=start,
    #     end=end,
    #     time_column=datetime_column
    # ).set_index(datetime_column)
    figure = plot_metrics_overview(df=series_comparison_statistics)

    save_figure(
        fig=figure,
        filename=output_filename.with_suffix(".png"),
        output_dir=output_directory,
        variable=None,  # No variable subdirectory for metrics overview
        close_after=False,
    )
