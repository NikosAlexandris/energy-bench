from pathlib import Path
import pandas as pd
from pandas import Timestamp
import matplotlib.pyplot as plt


def plot_assembled(
    csv_file: Path,
    start: Timestamp | None = None,
    end: Timestamp | None = None,
    output_png: Path | None = None,
):
    """
    Plot assembled total production (components + sum).
    Auto-detects all non-DateTime columns.
    """
    df = pd.read_csv(csv_file, parse_dates=["DateTime"]).set_index("DateTime")
    
    if start:
        df = df.loc[start:]
    if end:
        df = df.loc[:end]
    
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(10, 6), sharex=True)
    
    # Top: stacked area (components)
    df.iloc[:, :-1].plot.area(
        ax=ax1,
        linewidth=0,
        alpha=0.7,
        stacked=False,
        # stacked=True,
    )
    ax1.set_ylabel("GWh")
    ax1.set_title("Assembled Swiss production")
    ax1.legend(loc="upper left")
    
    # Bottom: total line + rolling mean
    df["Total"].plot(ax=ax2, linewidth=1.5, color="black", label="Total")
    df["Total"].rolling(168).mean().plot(ax=ax2, linewidth=1, color="red", alpha=0.7, label="7-day avg")
    ax2.set_ylabel("Total GWh")
    ax2.legend()
    
    plt.tight_layout()
    if output_png:
        plt.savefig(output_png, dpi=150, bbox_inches="tight")
        print(f"Saved to {output_png}")
    else:
        plt.show()
