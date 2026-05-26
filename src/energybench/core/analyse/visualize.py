"""
Visualization tools for bias detection results.
"""

from pathlib import Path
from typing import Optional

import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import numpy as np

from energybench.core.analyse.bias_detection import BiasDetectionResult
from matplotlib.lines import Line2D
from energybench.io.writing import save_figure


# Swiss-inspired color palette (Tufte style)
SWISS_RED = "#B55A52"
SOFT_GREY = "#808080"
MID_GREY = "0.65"
LIGHT_GREY = "#C7C7C7"
DARK_GREY = "0.35"

# Color-blind safe qualitative palette (Wong, Nature Methods 2011 — lightened for backgrounds)
CLUSTER_COLORS = ["#E69F00", "#56B4E9", "#009E73", "#CC79A7", "#0072B2"]


def set_tufte_style():
    """Apply Tufte-inspired minimalist style with Swiss colors."""
    plt.rcParams.update(
        {
            "axes.spines.top": False,
            "axes.spines.right": False,
            "axes.spines.left": True,
            "axes.spines.bottom": True,
            "axes.grid": True,
            "grid.color": "0.85",
            "grid.linestyle": "-",
            "grid.linewidth": 0.5,
            "axes.edgecolor": DARK_GREY,
            "axes.linewidth": 0.8,
            "xtick.labelsize": 9,
            "ytick.labelsize": 9,
            "xtick.color": "0.25",
            "ytick.color": "0.25",
            "xtick.major.size": 3,
            "ytick.major.size": 3,
            "xtick.major.width": 0.6,
            "ytick.major.width": 0.6,
            "axes.labelsize": 9,
            "axes.labelcolor": "0.2",
            "axes.titlesize": 11,
            "axes.titleweight": "normal",
            "legend.fontsize": 8,
            "legend.frameon": False,
            "figure.facecolor": "white",
            "axes.facecolor": "white",
        }
    )


def apply_spine_style(ax):
    """Apply spine styling to an axes object."""
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.spines["left"].set_linewidth(0.6)
    ax.spines["bottom"].set_linewidth(0.6)
    ax.spines["left"].set_color(DARK_GREY)
    ax.spines["bottom"].set_color(DARK_GREY)


def _draw_cluster_bands(ax, clusters):
    """Draw soft background bands for each cluster on a time-axis axes.

    Each cluster gets a pastel vertical band across the full y-range.
    Bands are drawn below data lines (zorder=-10) with no border.
    """
    for i, cluster in enumerate(clusters):
        color = CLUSTER_COLORS[i % len(CLUSTER_COLORS)]
        for start, end in cluster.periods:
            ax.axvspan(start, end, alpha=0.15, color=color, lw=0, zorder=-10)


def plot_bias_detection_overview(
    result: BiasDetectionResult,
    output_path: Optional[Path] = None,
    figsize: tuple[float, float] = (16, 10),
    dpi: int = 100,
) -> None:
    """
    Create comprehensive visualization of bias detection results.

    6-panel layout:
    Row 1: Daily Comparison, Bias %, Error metrics
    Row 2: Shape similarity, Correlation Stability (or empty)
    Row 3: Recommended Methods timeline (full width, with confidence)

    Parameters
    ----------
    result : BiasDetectionResult
        Detection results to visualize
    output_path : Path, optional
        Path to save figure
    figsize : tuple
        Figure size in inches
    dpi : int
        Resolution for saved figure
    """
    set_tufte_style()

    # Extract data from windows
    if not result.rolling_windows:
        print("No rolling windows to plot")
        return

    timestamps = [w.start for w in result.rolling_windows]
    bias_pct = [w.bias_pct for w in result.rolling_windows]
    mae = [w.mae for w in result.rolling_windows]
    rmse = [w.rmse for w in result.rolling_windows]
    pearson = [w.pearson for w in result.rolling_windows]
    mean_indicator = [w.mean_indicator for w in result.rolling_windows]
    mean_target = [w.mean_target for w in result.rolling_windows]

    # Method colors (Swiss palette)
    method_colors = {
        "scaling": LIGHT_GREY,
        "benchmarking": SWISS_RED,
        "kalman": SOFT_GREY,
    }

    # Create figure with 3 rows (two full rows + slim timeline row)
    fig = plt.figure(figsize=figsize)
    gs = fig.add_gridspec(
        3, 3,
        height_ratios=[0.65, 0.65, 0.3],
        hspace=0.3, wspace=0.28,
        left=0.07, right=0.97, top=0.88, bottom=0.06,
    )

    # Row 1 — "How different are the series?"
    ax1 = fig.add_subplot(gs[0, 0])  # Daily means
    ax2 = fig.add_subplot(gs[0, 1])  # Bias %
    ax3 = fig.add_subplot(gs[0, 2])  # Error metrics

    # Row 2 — "How reliable is the relationship?"
    ax4 = fig.add_subplot(gs[1, 0])  # Shape similarity
    ax5 = fig.add_subplot(gs[1, 1])  # Correlation stability
    ax6 = fig.add_subplot(gs[1, 2])  # (spare)

    # Row 3 — "What to do?" (full width)
    ax7 = fig.add_subplot(gs[2, :])

    # Apply spine styling
    for ax in [ax1, ax2, ax3, ax4, ax5, ax6, ax7]:
        apply_spine_style(ax)

    # Cluster bands on all time-based panels
    if result.clusters:
        for ax in [ax1, ax2, ax3, ax4, ax5]:
            _draw_cluster_bands(ax, result.clusters)

    # Panel 1: Daily means — the raw data
    ax1.plot(timestamps, mean_indicator, linewidth=1.2, color=LIGHT_GREY, alpha=0.9, label="Indicator")
    ax1.plot(timestamps, mean_target, linewidth=1.2, color=SWISS_RED, alpha=0.9, label="Target")
    ax1.set_ylabel("Daily mean (GWh)", fontweight="normal")
    ax1.set_title("Daily means", fontweight="normal", pad=4)
    ax1.legend(loc="upper right", fontsize=8, frameon=False)
    ax1.grid(True, alpha=0.3, linewidth=0.5)

    # Panel 2: Bias %
    ax2.plot(timestamps, bias_pct, "o-", color=SWISS_RED, linewidth=1.5, markersize=3, alpha=0.8)
    ax2.axhline(y=0, color=MID_GREY, linestyle="-", alpha=0.8, linewidth=1)
    ax2.axhline(y=5, color=SOFT_GREY, linestyle=":", alpha=0.6, linewidth=0.8)
    ax2.axhline(y=-5, color=SOFT_GREY, linestyle=":", alpha=0.6, linewidth=0.8)
    ax2.fill_between(timestamps, -5, 5, alpha=0.08, color=LIGHT_GREY)
    for cp in result.changepoints:
        if cp.metric_changed == "bias_pct":
            ax2.axvline(x=cp.timestamp, color=SWISS_RED, linestyle="--", alpha=0.4, linewidth=1)
    ax2.set_ylabel("Bias (%)", fontweight="normal")
    ax2.set_title("Bias over time", fontweight="normal", pad=4)
    ax2.grid(True, alpha=0.3, linewidth=0.5)

    # Panel 3: Error metrics
    ax3.plot(timestamps, mae, "o-", linewidth=1.5, markersize=3, label="MAE", color=SOFT_GREY, alpha=0.8)
    ax3.plot(timestamps, rmse, "s-", linewidth=1.5, markersize=3, label="RMSE", color=MID_GREY, alpha=0.8)
    for cp in result.changepoints:
        if cp.metric_changed in ["mae", "rmse"]:
            ax3.axvline(x=cp.timestamp, color=SWISS_RED, linestyle="--", alpha=0.4, linewidth=1)
    ax3.set_ylabel("Error (GWh)", fontweight="normal")
    ax3.set_title("Error metrics", fontweight="normal", pad=4)
    ax3.legend(loc="upper right", fontsize=8, frameon=False)
    ax3.grid(True, alpha=0.3, linewidth=0.5)

    # Panel 4: Shape similarity (correlation)
    ax4.plot(timestamps, pearson, "o-", linewidth=1.5, markersize=3, color=SOFT_GREY, alpha=0.8)
    ax4.axhline(y=0.9, color=SWISS_RED, linestyle=":", alpha=0.5, linewidth=0.8)
    ax4.axhline(y=0.7, color=SOFT_GREY, linestyle=":", alpha=0.5, linewidth=0.8)
    ax4.fill_between(timestamps, 0.9, 1.0, alpha=0.08, color=LIGHT_GREY)
    for cp in result.changepoints:
        if cp.metric_changed == "pearson":
            ax4.axvline(x=cp.timestamp, color=SWISS_RED, linestyle="--", alpha=0.4, linewidth=1)
    ax4.set_ylabel("Correlation", fontweight="normal")
    ax4.set_title("Shape similarity", fontweight="normal", pad=4)
    ax4.set_ylim(0, 1.05)
    ax4.grid(True, alpha=0.3, linewidth=0.5)

    # Panel 5: Correlation stability (derivative of panel 4)
    if len(pearson) > 5:
        window = 5
        corr_stability = []
        corr_timestamps = []
        for i in range(len(pearson) - window + 1):
            corr_window = pearson[i : i + window]
            corr_stability.append(np.std(corr_window))
            corr_timestamps.append(timestamps[i + window // 2])
        ax5.plot(corr_timestamps, corr_stability, "o-", linewidth=1.5, markersize=3, color=SOFT_GREY, alpha=0.8)
        ax5.axhline(y=0.05, color=SWISS_RED, linestyle=":", alpha=0.5, linewidth=0.9, label="Stable")
        ax5.fill_between(corr_timestamps, 0, 0.05, alpha=0.08, color=LIGHT_GREY)
    ax5.set_ylabel("Correlation σ", fontweight="normal")
    ax5.set_title("Correlation stability", fontweight="normal", pad=8)
    ax5.legend(loc="upper right", fontsize=8, frameon=False)
    ax5.grid(True, alpha=0.3, linewidth=0.5)

    # Panel 6: Bias vs correlation scatter — colored by cluster
    if result.clusters:
        # Assign each window to a cluster
        cluster_of_window = [-1] * len(timestamps)
        for ci, cl in enumerate(result.clusters):
            for start, end in cl.periods:
                for i, ts in enumerate(timestamps):
                    if start <= ts <= end:
                        cluster_of_window[i] = ci
        scatter_colors = [
            CLUSTER_COLORS[ci % len(CLUSTER_COLORS)] if ci >= 0 else SOFT_GREY
            for ci in cluster_of_window
        ]
    else:
        scatter_colors = [SOFT_GREY] * len(timestamps)
    ax6.scatter(bias_pct, pearson, c=scatter_colors, s=12, alpha=0.8, edgecolors="none", zorder=5)
    ax6.axvline(x=0, color=MID_GREY, linestyle="-", alpha=0.5, linewidth=0.8)
    ax6.axhline(y=0.9, color=SWISS_RED, linestyle=":", alpha=0.4, linewidth=0.6)
    ax6.axhline(y=0.7, color=SOFT_GREY, linestyle=":", alpha=0.4, linewidth=0.6)
    ax6.set_xlabel("Bias (%)", fontweight="normal")
    ax6.set_ylabel("Correlation", fontweight="normal")
    ax6.set_title("Bias vs correlation", fontweight="normal", pad=4)
    ax6.set_ylim(0, 1.05)
    ax6.grid(True, alpha=0.3, linewidth=0.5)

    # Cluster legend on scatter panel (lower-right)
    if result.clusters:
        # ax6.text(
        #     0.98, 0.03, "Clusters", transform=ax6.transAxes, fontsize=9,
        #     color=DARK_GREY, va="bottom", ha="right", fontweight="bold",
        # )
        for i, cl in enumerate(result.clusters):
            color = CLUSTER_COLORS[i % len(CLUSTER_COLORS)]
            # y = 0.03 + 0.13 * (len(result.clusters) - i)
            y = 0.08 * (len(result.clusters) - i)
            ax6.plot(0.96, y, "s", color=color, markersize=15,
                     transform=ax6.transAxes, clip_on=False, zorder=20)
            ax6.text(
                0.88, y,
                f"Cluster {i}:  {cl.n_periods} win  bias {cl.mean_bias_pct:+.0f}%  r {cl.mean_pearson:.2f}",
                transform=ax6.transAxes, fontsize=8, color=DARK_GREY,
                va="center", ha="right",
            )

    # Panel 7: Methods timeline — y-axis encodes confidence
    if result.recommendations:
        sorted_recs = sorted(result.recommendations, key=lambda x: x.start)
        present_methods = sorted({rec.recommended_method for rec in sorted_recs})

        for rec in sorted_recs:
            color = method_colors.get(rec.recommended_method, SOFT_GREY)
            y = rec.confidence

            # Horizontal line at confidence level
            ax7.plot([rec.start, rec.end], [y, y], color=color, linewidth=2.5, alpha=0.8, solid_capstyle="round")

            # Dot at start and end of each segment
            ax7.plot(rec.start, y, "o", color=color, markersize=4, alpha=0.9)
            ax7.plot(rec.end, y, "o", color=color, markersize=4, alpha=0.9)

        dummy_handles = [Line2D([0], [0], alpha=0) for _ in present_methods]
        legend = ax7.legend(
            handles=dummy_handles,
            labels=[m.replace("_", " ").title() for m in present_methods],
            loc="lower left", fontsize=11, ncol=len(present_methods),
            frameon=False, handlelength=0, handletextpad=0,
        )
        for text, method in zip(legend.get_texts(), present_methods):
            text.set_color(method_colors[method])

        ax7.set_ylabel("Confidence", fontweight="normal", fontsize=8)
        ax7.set_ylim(0, 1.1)
        ax7.set_yticks([0, 0.25, 0.5, 0.75, 1.0])
        ax7.yaxis.grid(True, alpha=0.2, linewidth=0.4)
    else:
        ax7.text(0.5, 0.5, "No recommendations generated", ha="center", va="center",
                 transform=ax7.transAxes, fontsize=9, color=SOFT_GREY)
        ax7.set_yticks([])

    ax7.set_xlabel("Date", fontweight="normal")
    ax7.set_title("Recommended adjustment methods", fontweight="normal", pad=6)
    ax7.grid(True, alpha=0.15, axis="x", linewidth=0.4)

    # X-axis: row 1 hides labels; row 2 gets compact horizontal labels; row 3 rotated
    for ax in [ax1, ax2, ax3]:
        ax.tick_params(axis="x", labelbottom=False)
    for ax in [ax4, ax5]:
        ax.tick_params(axis="x", labelsize=7)
    for label in ax7.get_xticklabels():
        label.set_rotation(45)
        label.set_ha("right")
    ax7.xaxis.set_tick_params(pad=2)

    # Overall title
    fig.suptitle(
        f"Bias Detection Analysis: {result.variable}\n\n"
        f"Overall Bias: {result.overall_bias_pct:+.2f}% | "
        f"MAE: {result.overall_mae:.2f} | "
        f"RMSE: {result.overall_rmse:.2f} | "
        f"Changepoints: {len(result.changepoints)} | "
        f"Clusters: {len(result.clusters)}",
        fontsize=12,
        fontweight="normal",
        y=0.975,
        linespacing=1.4,
    )

    if output_path:
        save_figure(fig=fig, filename=output_path.name, output_dir=output_path.parent,
                    variable=None, close_after=True, dpi=dpi)
    else:
        plt.show()
        plt.close()


def plot_recommendation_timeline(
    result: BiasDetectionResult,
    output_path: Optional[Path] = None,
    figsize: tuple[float, float] = (14, 6),
    dpi: int = 100,
) -> None:
    """
    Create a timeline view of recommendations with confidence levels (Swiss style).

    Parameters
    ----------
    result : BiasDetectionResult
        Detection results with recommendations
    output_path : Path, optional
        Path to save figure
    figsize : tuple
        Figure size in inches
    dpi : int
        Resolution for saved figure
    """
    set_tufte_style()

    if not result.recommendations:
        print("No recommendations to visualize")
        return

    fig, ax = plt.subplots(figsize=figsize)

    # Apply spine styling
    apply_spine_style(ax)

    # Method colors (Swiss palette)
    method_colors = {
        "scaling": LIGHT_GREY,
        "benchmarking": SWISS_RED,
        "kalman": SOFT_GREY,
    }

    # Sort recommendations by start date
    sorted_recs = sorted(result.recommendations, key=lambda x: x.start)

    # Plot each recommendation
    for i, rec in enumerate(sorted_recs):
        duration = (rec.end - rec.start).days
        color = method_colors.get(rec.recommended_method, SOFT_GREY)

        # Bar height based on confidence
        height = rec.confidence

        ax.barh(
            i,
            duration,
            left=rec.start,
            height=height,
            color=color,
            alpha=0.8,
            edgecolor=DARK_GREY,
            linewidth=0.6,
        )

        # Add method label
        mid_point = rec.start + (rec.end - rec.start) / 2
        method_display = rec.recommended_method.replace("_", "\n")
        text_color = "white" if rec.recommended_method == "benchmarking" else "0.2"
        ax.text(
            mid_point,
            i,
            method_display,
            ha="center",
            va="center",
            fontsize=7,
            fontweight="normal",
            color=text_color,
        )

        # Add confidence on the right
        ax.text(
            rec.end,
            i,
            f" {rec.confidence:.0%}",
            ha="left",
            va="center",
            fontsize=8,
            fontweight="normal",
            color=DARK_GREY,
        )

    # Create legend
    legend_patches = [
        mpatches.Patch(color=color, label=method.replace("_", " ").title(), alpha=0.8)
        for method, color in method_colors.items()
    ]
    ax.legend(handles=legend_patches, loc="lower left", fontsize=9, ncol=2, frameon=False)

    ax.set_xlabel("Date", fontsize=10, fontweight="normal")
    ax.set_ylabel("Recommendation #", fontsize=10, fontweight="normal")
    ax.set_title(
        f"Adjustment Method Recommendations: {result.variable}\nBar height = confidence level",
        fontsize=12,
        fontweight="normal",
        pad=12,
    )
    ax.set_yticks(range(len(sorted_recs)))
    ax.set_yticklabels([f"#{i + 1}" for i in range(len(sorted_recs))])
    ax.grid(True, alpha=0.3, axis="x", linewidth=0.5)

    fig.autofmt_xdate(rotation=45, ha="right")
    plt.tight_layout()

    if output_path:
        save_figure(fig=fig, filename=output_path.name, output_dir=output_path.parent,
                    variable=None, close_after=True, dpi=dpi)
    else:
        plt.show()
        plt.close()
