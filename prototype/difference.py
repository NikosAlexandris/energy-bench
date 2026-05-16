from pathlib import Path
import matplotlib.pyplot as plt


def plot_series_difference(
    target_series,
    benchmarked_series,
    data_source: str,
    electricity_generation_type: str,
    frequency: str,
    target_series_label: str = "Target series",
    benchmarked_series_label: str = "Benchmarked series",
    units: str = "GWh",
    xlabel: str = "Time",
    output_directory: Path = Path("output"),
) -> None:
    """
    """
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 8), sharex=True, height_ratios=[3, 1])

    benchmarked_series.plot(
        ax=ax1,
        label=f"{benchmarked_series_label} {frequency} sum",
        color="tab:blue",
        linewidth=2.5,
    )
    target_series.plot(
        ax=ax1,
        label=target_series_label,
        color="tab:orange",
        linestyle="None",
        marker="o",
        markersize=7,
        markerfacecolor="white",
        markeredgewidth=2,
    )
    ax1.set_title(f"{electricity_generation_type} {frequency} totals: benchmarked vs {data_source}")
    ax1.set_ylabel(units)
    ax1.grid(True, alpha=0.3)
    ax1.legend()

    difference = benchmarked_series - target_series
    difference.plot(ax=ax2, color="tab:red", marker="o", linewidth=1.5)
    ax2.axhline(0, color="black", linestyle="--", linewidth=1)
    ax2.set_title(f"Difference of {frequency} series")
    ax2.set_ylabel(units)
    ax2.set_xlabel(xlabel)
    ax2.grid(True, alpha=0.3)

    plt.tight_layout()
    output_directory.mkdir(parents=True, exist_ok=True)
    output_filename = f"{electricity_generation_type.lower()}_validation_with_difference.png"
    output_path = output_directory / output_filename
    plt.savefig(output_path, dpi=150, bbox_inches="tight")

    print(f"Plot saved as '{output_path}'")
