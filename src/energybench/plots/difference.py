from pathlib import Path
from matplotlib.figure import Figure
import matplotlib.pyplot as plt
import pandas as pd

LESS_THAN_BLACK = "0.2"
SWISS_RED = "#B55A52"
DARK_GREY = "#212121"
SOFT_GREY = "#808080"
MID_GREY = "0.65"


def _text_width_in_figcoords(fig, text_obj, renderer) -> float:
    bbox = text_obj.get_window_extent(renderer=renderer)
    fig_width_px = fig.get_figwidth() * fig.dpi
    return bbox.width / fig_width_px


def plot_series_difference(
    benchmarked_series: pd.Series,
    target_series: pd.Series,
    electricity_generation_type: str,
    frequency: str,
    benchmarked_data_source: str | None = None,
    target_data_source: str | None = None,
    benchmarked_series_label: str | None = "Benchmarked",
    target_series_label: str | None = "Target",
    units: str = "GWh",
    xlabel: str = "",
) -> Figure:
    """
    """
    # Series
    benchmarked_series = benchmarked_series.sort_index()
    target_series = target_series.sort_index()
    difference = (benchmarked_series - target_series).rename("difference")

    # Configure the figure
    fig, (ax_top, ax_diff) = plt.subplots(
        2,
        1,
        figsize=(11, 4),
        sharex=True,
        height_ratios=[2.2, 1],
        gridspec_kw={"hspace": 0.04},
    )

    # Minimal axis styling
    for ax in (ax_top, ax_diff):
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
    ax_top.step(
        target_series.index,
        target_series.values,
        where="mid",
        color=SWISS_RED,
        linewidth=0.7,
        alpha=0.9,
    )

    # Then the high-frequency series
    # Top: benchmarked hourly
    ax_top.plot(
        benchmarked_series.index,
        benchmarked_series.values,
        color=MID_GREY,
        linewidth=4,
        alpha=0.5,
    )
    # Mark missing values with red dots
    import numpy as np
    missing_mask = benchmarked_series.isna()
    if missing_mask.any():
        print(f"Missing value in {benchmarked_series}")
        missing_label=f'Missing ({missing_mask.sum()} points)'
        ax_top.scatter(benchmarked_series.index[missing_mask],
                   np.full(missing_mask.sum(), benchmarked_series.min()),
                   color='red', marker='o', s=50,
                   # label=f'Missing ({missing_mask.sum()} points)',
                   zorder=5,
                )

    bench_rolling = benchmarked_series.rolling(24, center=True, min_periods=1).mean()
    ax_top.plot(
        bench_rolling.index,
        bench_rolling.values,
        color=DARK_GREY,
        linewidth=0.4,
    )

    ax_top.set_ylabel(units, fontsize=9, color=LESS_THAN_BLACK)
    ax_top.tick_params(axis="x", length=0)
    ax_top.spines["bottom"].set_visible(False)

    title_y = 0.965
    subtitle_y = 0.918

    bench_label = benchmarked_series_label or benchmarked_data_source or "Benchmarked"
    target_label = target_series_label or target_data_source or "Target"
    rolling_label = "24h rolling mean"

    x0 = 0.08
    gap = 0.008  # figure-coordinate gap
    title_fontsize = 12

    # Title
    title = fig.text(
        x=x0,
        y=title_y,
        s=f"{electricity_generation_type} · {frequency}",
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

    if len(benchmarked_series.index) > 0:
        start_candidates.append(pd.Timestamp(benchmarked_series.index.min()))
        end_candidates.append(pd.Timestamp(benchmarked_series.index.max()))

    if len(target_series.index) > 0:
        start_candidates.append(pd.Timestamp(target_series.index.min()))
        end_candidates.append(pd.Timestamp(target_series.index.max()))

    if start_candidates and end_candidates:
        start_year = min(start_candidates).year
        end_year = max(end_candidates).year
        if start_year == end_year:
            temporal_coverage_label = f"{start_year}"
        else:
            temporal_coverage_label = f"{start_year}–{end_year}"
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
        color=LESS_THAN_BLACK,
    )

   # First label
    label_1 = fig.text(
        x0, subtitle_y,
        f"— {bench_label}",
        ha="left",
        va="top",
        fontsize=8,
        color=SOFT_GREY,
    )

    fig.canvas.draw()
    renderer = fig.canvas.get_renderer()
    label_1_width = _text_width_in_figcoords(fig, label_1, renderer)

    rolling_label_x = x0 + label_1_width + gap
    rolling_label = fig.text(
        rolling_label_x,
        subtitle_y,
        f"— {rolling_label}",
        ha="left",
        va="top",
        fontsize=8,
        color=DARK_GREY,
    )

    fig.canvas.draw()
    renderer = fig.canvas.get_renderer()
    rolling_label_width = _text_width_in_figcoords(fig, rolling_label, renderer)

    # Second label
    label_2_x = rolling_label_x + rolling_label_width + gap
    label_2 = fig.text(
        label_2_x, subtitle_y,
        f"— {target_label}",
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
                missing_label_x, subtitle_y,
            f"o {missing_label}",
            ha="left",
            va="top",
            fontsize=8,
            color=SWISS_RED,
        )

    # Bottom panel
    ax_diff.axhline(0, color="#9C9C9C", linewidth=0.7)
    ax_diff.plot(
        difference.index,
        difference.values,
        # color="#8F3D37",
        color=SOFT_GREY,
        linewidth=0.85,
        linestyle=(0, (0.5, 1)),
        solid_capstyle="round",
    )

    ax_diff.fill_between(
        difference.index,
        0,
        difference.values,
        color="#D9C9C7",
        alpha=0.35,
        linewidth=0,
    )

    # Small note about what lower panel is
    fig.text(
        0.09,
        0.11,
        # f"Daily {benchmarked_series_label} - {target_series_label}",
        f"Difference between low-frequency & aggregated high-frequency series",
        ha="left",
        va="bottom",
        fontsize=7,
        color="0.45",
    )

    ax_diff.set_ylabel("Δ", fontsize=9, color=LESS_THAN_BLACK)
    ax_diff.set_xlabel(xlabel, fontsize=9, color=LESS_THAN_BLACK)
    ax_diff.yaxis.grid(True, color="0.9", linewidth=0.5)
    ax_diff.xaxis.grid(False)

    if not benchmarked_series_label and not target_series_label:
        # Colored subtitle row
        fig.text(
            0.08, subtitle_y,
            benchmarked_data_source or benchmarked_series_label,
            ha="left",
            va="top",
            fontsize=8,
            color="#7A7A7A",   # benchmarked series grey
        )

        fig.text(
            0.205, subtitle_y,
            "—",
            ha="left",
            va="top",
            fontsize=8,
            color="0.65",
        )

        fig.text(
            0.22, subtitle_y,
            target_data_source or target_series_label,
            ha="left",
            va="top",
            fontsize=8,
            color="#B55A52",   # target series muted Swiss red
        )
    plt.subplots_adjust(left=0.08, right=0.98, top=0.88, bottom=0.10)

    return fig
