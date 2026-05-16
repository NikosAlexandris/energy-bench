import matplotlib.pyplot as plt
from pandas import DataFrame
import pandas as pd
import matplotlib.dates as mdates
from pathlib import Path


SWISS_RED = "#B55A52"
SOFT_GREY = "#808080"
MID_GREY = "0.65"


def _text_width_in_figcoords(fig, text_obj, renderer) -> float:
    bbox = text_obj.get_window_extent(renderer=renderer)
    fig_width_px = fig.get_figwidth() * fig.dpi
    return bbox.width / fig_width_px


def plot_series_before_and_after(
    dataframe: DataFrame,
    original_series: pd.Series,
    adjusted_series: pd.Series,
    electricity_generation_type: str,
    original_series_label: str | None = None,
    adjusted_series_label: str | None = None,
    data_source: str | None = None,
    reconstruction_method: str | None = None,
    frequency: str = "hourly",
    units: str = "GWh",
    xlabel: str = "Time",
) -> Figure:
    """ """
    # Series
    original_series = dataframe[original_series].sort_index()
    adjusted_series = dataframe[adjusted_series].sort_index()

    # Configure the figure
    fig, ax = plt.subplots(
        1,
        1,
        figsize=(11, 3.2),
        gridspec_kw={"hspace": 0.04},
    )

    # Minimal axis styling
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.spines["left"].set_linewidth(0.6)
    ax.spines["bottom"].set_linewidth(0.6)
    ax.spines["left"].set_color("0.35")
    ax.spines["bottom"].set_color("0.35")
    ax.tick_params(axis="both", labelsize=9, colors="0.25", length=3, width=0.6)
    ax.grid(False)

    # First the low-frequency series
    # Daily target in muted Swiss red, fine dashed
    ax.plot(
        adjusted_series.index,
        adjusted_series.values,
        # where="mid",
        color=SWISS_RED,
        linewidth=0.5,
        alpha=0.9,
    )

    # Then the high-frequency series
    # Top: benchmarked hourly
    ax.plot(
        original_series.index,
        original_series.values,
        color="#C7C7C7",
        linewidth=0.5,
    )

    # Mark missing values with red dots
    import numpy as np

    missing_mask = original_series.isna()
    if missing_mask.any():
        missing_label = f"Missing ({missing_mask.sum()} points)"
        ax.scatter(
            original_series.index[missing_mask],
            np.full(missing_mask.sum(), original_series.min()),
            color="red",
            marker="o",
            s=50,
            # label=f'Missing ({missing_mask.sum()} points)',
            zorder=5,
        )

    ax.set_ylabel(units, fontsize=9, color="0.2")
    ax.tick_params(axis="x", length=0)
    # ax.spines["bottom"].set_visible(False)

    title_y = 0.965
    subtitle_y = 0.918

    before_label = original_series_label or "Original"
    after_label = adjusted_series_label or data_source or "Adjusted"
    if reconstruction_method:
        after_label += f" via {reconstruction_method}"

    x0 = 0.08
    gap = 0.008  # figure-coordinate gap
    title_fontsize = 12

    title = f"{electricity_generation_type} {frequency} profile"

    # Title
    title = fig.text(
        x=x0,
        y=title_y,
        s=title,
        ha="left",
        va="top",
        fontsize=title_fontsize,
        color="0.1",
    )

    # Force a draw so text extents are available
    fig.canvas.draw()
    renderer = fig.canvas.get_renderer()
    title_width = _text_width_in_figcoords(fig, title, renderer)

    # Temporal coverage
    start_candidates = []
    end_candidates = []

    if len(original_series.index) > 0:
        start_candidates.append(pd.Timestamp(original_series.index.min()))
        end_candidates.append(pd.Timestamp(original_series.index.max()))

    if len(adjusted_series.index) > 0:
        start_candidates.append(pd.Timestamp(adjusted_series.index.min()))
        end_candidates.append(pd.Timestamp(adjusted_series.index.max()))

    if start_candidates and end_candidates:
        start_year = min(start_candidates).year
        end_year = max(end_candidates).year
        if not start_year == end_year:
            temporal_coverage_label = f"{start_year}·{end_year}"
        else:
            temporal_coverage_label = start_year

    else:
        temporal_coverage_label = ""

    temporal_coverage_label_x = x0 + title_width + gap

    fig.text(
        x=temporal_coverage_label_x,
        y=title_y,
        s=temporal_coverage_label,
        ha="left",
        va="top",
        fontsize=title_fontsize,
        color="0.2",
    )

    # First label
    label_1 = fig.text(
        x0,
        subtitle_y,
        f"— {before_label}",
        ha="left",
        va="top",
        fontsize=8,
        color=SOFT_GREY,
    )

    fig.canvas.draw()
    renderer = fig.canvas.get_renderer()
    label_1_width = _text_width_in_figcoords(fig, label_1, renderer)

    # Second label
    label_2_x = x0 + label_1_width + gap
    label_2 = fig.text(
        label_2_x,
        subtitle_y,
        f"— {after_label}",
        ha="left",
        va="top",
        fontsize=8,
        color=SWISS_RED,
    )

    fig.canvas.draw()
    renderer = fig.canvas.get_renderer()
    label_2_width = _text_width_in_figcoords(fig, label_2, renderer)
    missing_label_x = label_2_x + label_2_width + gap
    if missing_mask.any():
        fig.text(
            missing_label_x,
            subtitle_y,
            f"o {missing_label}",
            ha="left",
            va="top",
            fontsize=8,
            color=SWISS_RED,
        )

    if not original_series_label and not adjusted_series_label:
        # Colored subtitle row
        fig.text(
            0.08,
            subtitle_y,
            data_source or original_series_label,
            ha="left",
            va="top",
            fontsize=8,
            color="#7A7A7A",  # Original series
        )

        fig.text(
            0.22,
            subtitle_y,
            data_source or adjusted_series_label,
            ha="left",
            va="top",
            fontsize=8,
            color=SWISS_RED,  # Adjusted series
        )
    fig.subplots_adjust(left=0.08, right=0.98, top=0.88, bottom=0.10)

    return fig
