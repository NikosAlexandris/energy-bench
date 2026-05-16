from matplotlib.figure import Figure
import pandas as pd
import matplotlib.pyplot as plt


def set_tufte_style():
    plt.style.use("default")
    plt.rcParams.update(
        {
            "figure.figsize": (7, 4),
            "axes.spines.top": False,
            "axes.spines.right": False,
            "axes.grid": True,
            "grid.color": "0.85",
            "grid.linestyle": "-",
            "grid.linewidth": 0.5,
            "axes.edgecolor": "0.3",
            "axes.linewidth": 0.8,
            "axes.titlesize": 20,
            "axes.labelsize": 15,
            "xtick.labelsize": 12,
            "ytick.labelsize": 12,
            "legend.fontsize": 14,
            "lines.linewidth": 1.0,
            "lines.markersize": 8,
        }
    )


def suggest_method(row: pd.Series) -> str:
    pearson = row["pearson"]
    nrmse = row["nrmse_mean"]
    bias = row["bias_pct"]

    if pearson > 0.97 and nrmse < 0.1 and abs(bias) < 5:
        return "none_or_constant"
    elif pearson > 0.9 and nrmse < 0.5 and abs(bias) < 35:
        return "daily_scaling"
    elif pearson > 0.7:
        return "benchmarking"
    else:
        return "advanced"


def plot_metrics_overview(
    df: pd.DataFrame,
    title_suffix: str = "",
) -> Figure:
    """
    df must have columns:
      Category, pearson, nrmse_mean, bias_pct, mae
    Optional columns: start, end (for temporal extent)
    """
    set_tufte_style()
    df = df.copy()

    # Handle missing or empty category names
    if "category" not in df.columns or df["category"].isna().all():
        df["category"] = [f"Series {i + 1}" for i in range(len(df))]
    else:
        # Replace None/NaN/empty strings with default names
        df["category"] = df["category"].fillna("").astype(str)
        df.loc[df["category"] == "", "category"] = [
            f"Series {i + 1}" for i in range(len(df[df["category"] == ""]))
        ]

    df["method"] = df.apply(suggest_method, axis=1)

    # Extract temporal extent if available
    temporal_extent = ""
    if "start" in df.columns and "end" in df.columns:
        start_dates = pd.to_datetime(df["start"])
        end_dates = pd.to_datetime(df["end"])
        overall_start = start_dates.min()
        overall_end = end_dates.max()
        temporal_extent = (
            f" ({overall_start.strftime('%Y-%m-%d')} to {overall_end.strftime('%Y-%m-%d')})"
        )

    figure, axes = plt.subplots(1, 3, figsize=(14, 8), constrained_layout=True)

    # Panel 1: Pearson vs nRMSE (good = top-left)
    ax = axes[0]
    ax.scatter(df["nrmse_mean"], df["pearson"], color="0.2", s=80, alpha=0.6)
    for _, r in df.iterrows():
        label = str(r["category"]) if r["category"] else "Unknown"
        # Add more space between point and label (use "  " instead of " ")
        ax.text(
            r["nrmse_mean"],
            r["pearson"],
            f"  {label}",
            fontsize=12,
            ha="left",
            va="center",
            color="0.25",
        )
    ax.axvline(0.5, color="0.7", linestyle="--", linewidth=0.8, label="nRMSE threshold")
    ax.axhline(0.9, color="0.7", linestyle="--", linewidth=0.8, label="Pearson threshold")
    ax.set_xlabel("nRMSE (lower is better)")
    ax.set_ylabel("Pearson correlation (higher is better)")
    ax.set_title("Daily fit quality")
    # Move legend to lower left with no frame
    ax.legend(fontsize=10, loc="lower left", frameon=False)

    # Panel 2: Bias (%)
    ax = axes[1]
    order = df.sort_values("bias_pct")["category"].tolist()
    colors = ["red" if x < 0 else "blue" for x in df.sort_values("bias_pct")["bias_pct"]]
    ax.barh(range(len(df)), df.sort_values("bias_pct")["bias_pct"], color=colors, alpha=0.6)
    ax.axvline(0, color="0.3", linestyle="-", linewidth=1.5)
    ax.set_xlabel("Bias % (negative = underestimate)")
    ax.set_yticks(range(len(order)))
    ax.set_yticklabels(order)
    ax.set_title("Level bias")
    ax.grid(axis="x", alpha=0.3)

    # Panel 3: Shape MAE
    ax = axes[2]
    x_pos = range(len(df))
    ax.bar(x_pos, df["mae"], color="0.4", alpha=0.7)
    ax.set_xticks(x_pos)
    ax.set_xticklabels(df["category"], rotation=45, ha="right")
    ax.set_ylabel("MAE (GWh)")
    ax.set_title("Mean Absolute Error")
    ax.grid(axis="y", alpha=0.3)

    # Add title with temporal extent
    if title_suffix:
        figure.suptitle(f"Metrics overview {title_suffix}{temporal_extent}", fontsize=16)
    elif temporal_extent:
        figure.suptitle(f"Metrics overview{temporal_extent}", fontsize=16)

    return figure
