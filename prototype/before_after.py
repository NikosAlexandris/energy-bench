from pathlib import Path
import matplotlib.pyplot as plt
from pandas import DataFrame


def plot_series_before_and_after(
    dataframe: DataFrame,
    original_series: str,
    adjusted_series: str,
    data_source: str,
    electricity_generation_type: str,
    frequency: str = "hourly",
    units: str = "GWh",
    xlabel: str = "Time",
    output_directory: Path = Path("output"),
) -> None:
    """
    """
    fig, ax = plt.subplots(figsize=(14, 4))

    dataframe[original_series].plot(
        ax=ax,
        label=f"Original {data_source} {electricity_generation_type.lower()} {frequency} series",
        alpha=0.7,
    )
    dataframe[adjusted_series].plot(
        ax=ax,
        label=f"Adjusted benchmarked {electricity_generation_type.lower()} {frequency} series",
        alpha=0.7,
    )

    ax.set_title(f"{electricity_generation_type} {frequency} profile: Original vs Adjusted")
    ax.set_ylabel(units)
    ax.set_xlabel(xlabel)
    ax.grid(True, alpha=0.3)
    ax.legend()

    plt.tight_layout()
    output_directory.mkdir(parents=True, exist_ok=True)
    output_filename = f"{electricity_generation_type.lower()}_before_after_{frequency}.png"
    output_path = output_directory / output_filename
    plt.savefig(output_path, dpi=150, bbox_inches="tight")

    print(f"Plot saved as '{output_path}'")
