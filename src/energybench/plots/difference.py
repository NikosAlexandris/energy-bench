from pathlib import Path
import matplotlib.pyplot as plt
from matplotlib.ticker import MultipleLocator
import pandas as pd


# def plot_series_difference(
#     benchmarked_series,
#     target_series,
#     #
#     electricity_generation_type: str,
#     frequency: str,
#     #
#     benchmarked_data_source: str | None = None,
#     target_data_source: str | None = None,
#     benchmarked_series_label: str | None = "Benchmarked series",
#     target_series_label: str | None = "Target series",
#     #
#     units: str = "GWh",
#     xlabel: str = "Time",
#     output_filename: Path | None = None,
#     output_directory: Path = Path("output"),
# ) -> None:
#     """
#     """
#     fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 8), sharex=True, height_ratios=[3, 1])

#     benchmarked_series.plot(
#         ax=ax1,
#         label=f"{frequency} sum of {benchmarked_series_label}" or benchmarked_series_label,
#         color="tab:blue",
#         linewidth=2.5,
#     )
#     target_series.plot(
#         ax=ax1,
#         label=target_series_label,
#         color="tab:orange",
#         linestyle="None",
#         marker="o",
#         markersize=7,
#         markerfacecolor="white",
#         markeredgewidth=2,
#     )
#     ax1.set_title(f"{frequency} totals of {electricity_generation_type}")
#     # Subtitle below title (adjust y=0.98)
#     fig.text(
#         x=0.5,
#         y=0.92,
#         s=f"{benchmarked_data_source} vs {target_data_source}",
#         ha='center',
#         fontsize=11,
#         style='italic',
#     )
#     ax1.set_ylabel(units)
#     ax1.grid(True, alpha=0.3)
#     ax1.legend()

#     difference = benchmarked_series - target_series
#     difference.plot(ax=ax2, color="tab:red", marker="o", linewidth=1.5)
#     ax2.axhline(0, color="black", linestyle="--", linewidth=1)
#     ax2.set_title(f"Difference of {frequency} series")
#     ax2.set_ylabel(units)
#     ax2.set_xlabel(xlabel)
#     ax2.grid(True, alpha=0.3)

#     plt.tight_layout()
#     output_directory.mkdir(parents=True, exist_ok=True)
#     if output_filename is None:
#         output_filename = Path(f"{electricity_generation_type.lower()}_benchmarked_vs_target_difference")
#     output_path = output_directory / Path(output_filename).with_suffix(".png")
#     plt.savefig(output_path, dpi=150, bbox_inches="tight", facecolor="white")

#     print(f"Plot saved as '{output_path}'")



def plot_series_difference(
    benchmarked_series: pd.Series,
    target_series: pd.Series,
    electricity_generation_type: str,
    frequency: str,
    benchmarked_data_source: str | None = None,
    target_data_source: str | None = None,
    benchmarked_series_label: str | None = "Benchmarked series",
    target_series_label: str | None = "Target series",
    units: str = "GWh",
    xlabel: str = "Time",
    output_filename: Path | None = None,
    output_directory: Path = Path("output"),
) -> None:
    fig, (ax1, ax2) = plt.subplots(
        2, 1, figsize=(14, 4.5), sharex=True, height_ratios=[3, 1], gridspec_kw={"hspace": 0.08}
    )

    # Global Tufte styling
    for ax in [ax1, ax2]:
        ax.spines["top"].set_visible(False)
        ax.spines["right"].set_visible(False)
        ax.spines["left"].set_linewidth(0.5)
        ax.spines["bottom"].set_linewidth(0.5)

    # Main plot
    benchmarked_series.plot(
        ax=ax1, color="#2ca02c", linewidth=1.5, alpha=1.0, label=benchmarked_series_label
    )
    target_series.plot(
        ax=ax1,
        color="#d62728",
        marker="o",
        markersize=4,
        markerfacecolor="white",
        markeredgewidth=1,
        linewidth=0,
        alpha=1.0,
        label=target_series_label,
    )

    ax1.set_title(
        f"{electricity_generation_type} ({frequency})",
        fontsize=14, fontweight="normal", pad=10
    )
    ax1.set_ylabel(units, fontsize=12)
    ax1.tick_params(axis="both", which="major", labelsize=10)
    ax1.xaxis.set_major_locator(MultipleLocator(7))  # Weekly ticks
    ax1.legend(loc="upper left", frameon=False, fontsize=10)

    # Difference plot
    difference = benchmarked_series - target_series
    difference.plot(ax=ax2, color="#9467bd", linewidth=1.2, marker="o", markersize=3)
    ax2.axhline(0, color="black", linewidth=0.8)
    ax2.set_ylabel("Difference", fontsize=11)
    ax2.set_xlabel(xlabel, fontsize=11)
    ax2.tick_params(axis="both", which="major", labelsize=10)

    # Subtitle
    if benchmarked_data_source and target_data_source:
        fig.text(
            0.02, 0.95, f"{benchmarked_data_source} vs {target_data_source}",
            fontsize=10, style="italic", va="top",
            transform=fig.transFigure
        )

    plt.subplots_adjust(left=0.08, right=0.98, top=0.92, bottom=0.12)
    
    output_directory.mkdir(parents=True, exist_ok=True)
    if output_filename is None:
        output_filename = Path(f"{electricity_generation_type.lower()}_difference_{frequency}")
    output_path = output_directory / Path(output_filename).with_suffix(".png")
    plt.savefig(
        output_path,
        dpi=150,
        bbox_inches="tight",
        facecolor="white",
        edgecolor="none",
        pad_inches=0.1
    )
    plt.close()

    print(f"💾 Plot saved as '{output_path}'")
