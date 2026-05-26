from pathlib import Path
from energybench.core.plots.metrics import plot_metrics_overview
import pandas as pd
from energybench.io.writing import save_figure


def plot_comparison_metrics(
    series_comparison_csv: Path,
    output_directory: Path = Path("output"),
    output_filename: Path | None = None,
    quiet: bool = False,
):
    """
    Plot summary metrics from a CSV produced by compare series commands.
    """
    series_comparison_statistics = pd.read_csv(series_comparison_csv)
    figure = plot_metrics_overview(df=series_comparison_statistics)

    if output_filename is None:
        stem = series_comparison_csv.stem
        output_filename = Path(stem).with_suffix(".png")
        # Auto-place next to input CSV (preserves variable subdirectory)
        if output_directory == Path("output"):
            output_directory = series_comparison_csv.parent
    else:
        output_filename = output_filename.with_suffix(".png")

    save_figure(
        fig=figure,
        filename=output_filename,
        output_dir=output_directory,
        variable=None,
        close_after=False,
        quiet=quiet,
    )
