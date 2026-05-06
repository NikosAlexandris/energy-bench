from pathlib import Path
import matplotlib.pyplot as plt
from matplotlib.ticker import MultipleLocator
import matplotlib.dates as mdates
from pandas import DataFrame


def plot_series_before_and_after(
    dataframe: DataFrame,
    original_series: str,
    adjusted_series: str,
    electricity_generation_type: str,
    original_series_label: str | None = None,
    adjusted_series_label: str | None = None,
    data_source: str | None = None,
    frequency: str = "hourly",
    units: str = "GWh",
    xlabel: str = "Time",
    output_directory: Path = Path("output"),
) -> None:
    """ """
    fig, ax = plt.subplots(figsize=(14, 3.5), dpi=150)

    # Tufte: thin lines, no grid, minimal margins
    plt.style.use("default")
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.spines["left"].set_linewidth(0.5)
    ax.spines["bottom"].set_linewidth(0.5)

    # Plot lines
    original_series_label = (
        original_series_label or f"Original {data_source or 'high-frequency'}"
    )
    # original_series_label = original_series_label or (
    # f"Original {electricity_generation_type.lower()} {frequency} series" + 
    # (f" ({data_source})" if data_source else "")
    # )
    adjusted_series_label = adjusted_series_label or "Benchmarked"  # f"Adjusted {electricity_generation_type.lower()} {frequency} series"

    dataframe[original_series].plot(
        ax=ax, color="#1f77b4", linewidth=1.2, alpha=0.85, label=original_series_label
    )
    dataframe[adjusted_series].plot(
        ax=ax, color="#ff7f0e", linewidth=1.8, alpha=1.0, label=adjusted_series_label
    )

    # Tufte typography: no bold title, smaller labels
    ax.set_title(
    # f"Original vs Adjusted {electricity_generation_type} {frequency} profile",
        f"{electricity_generation_type} ({frequency})",
        fontsize=14,
        fontweight="normal",
        pad=10,
    )
    ax.set_ylabel(units, fontsize=12)
    ax.set_xlabel(xlabel, fontsize=11)

    # Minimal ticks
    ax.tick_params(axis="both", which="major", labelsize=10)
    ax.xaxis.set_major_locator(MultipleLocator(24))  # Daily ticks for hourly data

    # Legend: outside plot area
    ax.legend(loc="upper left", frameon=False, fontsize=10)

    # Tight layout with minimal margins
    plt.subplots_adjust(left=0.08, right=0.98, top=0.92, bottom=0.12)

    output_directory.mkdir(parents=True, exist_ok=True)
    output_filename = (
        f"{electricity_generation_type.lower()}_before_after_{frequency}.png"
    )
    output_path = output_directory / output_filename
    plt.savefig(
        output_path,
        dpi=150,
        bbox_inches="tight",
        facecolor="white",
        edgecolor="none",
        pad_inches=0.1,
    )
    plt.close()

    print(f"💾 Plot saved as '{output_path}'")



def plot_series_before_and_after(
    dataframe: DataFrame,
    original_series: str,
    adjusted_series: str,
    electricity_generation_type: str,
    original_series_label: str | None = None,
    adjusted_series_label: str | None = None,
    data_source: str | None = None,
    frequency: str = "hourly",
    units: str = "GWh",
    xlabel: str = "Time",
    output_directory: Path = Path("output"),
) -> None:
    fig, ax = plt.subplots(figsize=(14, 3.8), dpi=150)

    original_series_label = original_series_label or (
        f"Original {electricity_generation_type.lower()} {frequency} series"
        + (f" ({data_source})" if data_source else "")
    )
    adjusted_series_label = adjusted_series_label or (
        f"Adjusted {electricity_generation_type.lower()} {frequency} series"
    )

    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.spines["left"].set_linewidth(0.6)
    ax.spines["bottom"].set_linewidth(0.6)

    ax.plot(
        dataframe.index,
        dataframe[original_series],
        # color="0.55",
        linewidth=0.9,
        alpha=0.7,
        label=original_series_label,
        zorder=2,
    )
    ax.plot(
        dataframe.index,
        dataframe[adjusted_series],
        # color="0.10",
        linewidth=1.2,
        alpha=0.8,
        label=adjusted_series_label,
        zorder=3,
    )

    fig.suptitle(
        f"{electricity_generation_type} {frequency} profile",
        x=0.08,
        y=0.85,
        ha="left",
        fontsize=12,
        fontweight="normal",
    )



    ax.set_ylabel(units, fontsize=10)
    ax.set_xlabel(xlabel, fontsize=10)
    ax.grid(False)

    locator = mdates.AutoDateLocator(minticks=4, maxticks=8)
    formatter = mdates.ConciseDateFormatter(locator)
    ax.xaxis.set_major_locator(locator)
    ax.xaxis.set_major_formatter(formatter)

    ax.minorticks_off()
    ax.tick_params(axis="x", which="major", labelsize=9, length=3, width=0.6, colors="0.25")
    ax.tick_params(axis="y", which="major", labelsize=9, length=3, width=0.6, colors="0.25")

    ax.legend(
        loc="lower left",
        bbox_to_anchor=(0.0, 1.01),
        frameon=False,
        ncol=2,
        fontsize=9,
        handlelength=2.8,
        borderaxespad=0.0,
        columnspacing=1.5,
    )

    ax.margins(x=0.01)

    plt.tight_layout(rect=(0, 0, 1, 0.92))

    output_directory.mkdir(parents=True, exist_ok=True)
    output_filename = f"{electricity_generation_type.lower()}_before_after_{frequency}.png"
    output_path = output_directory / output_filename
    plt.savefig(
        output_path,
        dpi=150,
        bbox_inches="tight",
        facecolor="white",
        edgecolor="none",
        pad_inches=0.08,
    )
    plt.close()

    print(f"Plot saved as '{output_path}'")
