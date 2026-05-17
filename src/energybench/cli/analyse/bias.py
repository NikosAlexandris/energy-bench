"""
Function for automated bias detection.
"""

from pathlib import Path
from typing import Annotated, Optional

import cyclopts
import pandas as pd

from energybench.analyse.bias_detection import detect_bias_patterns
from energybench.analyse.visualize import (
    plot_bias_detection_overview,
    plot_cluster_characteristics,
    plot_recommendation_timeline,
)
from energybench.io.reading import read_csv
from energybench.core.configuration import get_variable_config
from energybench.core.utilities import sum_columns


def autodetect_bias_patterns(
    variable: Annotated[
        str,
        cyclopts.Parameter(help="Energy type to analyze (e.g., 'river', 'solar', 'nuclear')"),
    ],
    indicator_csv: Annotated[
        Path,
        cyclopts.Parameter(help="Path to high-frequency indicator CSV (hourly data)"),
    ],
    target_csv: Annotated[
        Path,
        cyclopts.Parameter(help="Path to low-frequency target CSV (daily reference data)"),
    ],
    start: Annotated[
        pd.Timestamp,
        cyclopts.Parameter(help="Start date (YYYY-MM-DD)"),
    ],
    end: Annotated[
        pd.Timestamp,
        cyclopts.Parameter(help="End date (YYYY-MM-DD)"),
    ],
    output_csv: Annotated[
        Optional[Path],
        cyclopts.Parameter(help="Output CSV path for recommendations"),
    ] = None,
    output_summary: Annotated[
        Optional[Path],
        cyclopts.Parameter(help="Output text file for summary report"),
    ] = None,
    output_plot: Annotated[
        Optional[Path],
        cyclopts.Parameter(help="Output path for visualization plot"),
    ] = None,
    output_clusters_plot: Annotated[
        Optional[Path],
        cyclopts.Parameter(help="Output path for cluster characteristics plot"),
    ] = None,
    output_timeline_plot: Annotated[
        Optional[Path],
        cyclopts.Parameter(help="Output path for recommendation timeline plot"),
    ] = None,
    window_size: Annotated[
        str,
        cyclopts.Parameter(help="Rolling window size (e.g., '30D', '60D')"),
    ] = "30D",
    step_size: Annotated[
        str,
        cyclopts.Parameter(help="Step between windows (e.g., '7D', '14D')"),
    ] = "7D",
    n_clusters: Annotated[
        int,
        cyclopts.Parameter(help="Number of clusters for period grouping"),
    ] = 3,
    changepoint_method: Annotated[
        str,
        cyclopts.Parameter(help="Changepoint detection method: 'threshold', 'binary_segmentation'"),
    ] = "threshold",
    changepoint_threshold: Annotated[
        float,
        cyclopts.Parameter(help="Threshold for changepoint detection (bias % change)"),
    ] = 5.0,
    indicator_time_column: Annotated[
        str,
        cyclopts.Parameter(help="DateTime column name in indicator CSV"),
    ] = "DateTime",
    target_time_column: Annotated[
        str,
        cyclopts.Parameter(help="Date column name in target CSV"),
    ] = "Date",
) -> None:
    """
    Detect bias patterns and recommend adjustment strategies for subperiods.
    
    This command performs comprehensive analysis:
    - Rolling window bias analysis
    - Changepoint detection
    - Period clustering
    - Method recommendations
    
    Example:
        nrgbnc analyze bias-patterns river \\
            --high-frequency-csv data/hourly_indicator.csv \\
            --low-frequency-csv data/daily_target.csv \\
            --start 2018-01-01 \\
            --end 2024-12-31 \\
            --output-csv output/river_bias_analysis.csv \\
            --output-summary output/river_bias_summary.txt
    """
    print(f"🔍 Analyzing bias patterns for {variable}...")
    print(f"   Period: {start.date()} to {end.date()}")
    print(f"   Window size: {window_size}, Step: {step_size}")

    # Get variable configuration
    config = get_variable_config(variable, strict=True)

    # Read high-frequency data
    print(f"📖 Reading indicator data from {indicator_csv}...")
    hf_df = read_csv(
        indicator_csv,
        start=start,
        end=end,
        time_column=indicator_time_column,
    )

    # Sum indicator columns
    indicator = sum_columns(
        hf_df,
        config["indicator_types_present"],
        label=f"{variable}_indicator",
    ).loc[start:end]

    # Read low-frequency data
    print(f"📖 Reading target data from {target_csv}...")
    lf_df = read_csv(
        target_csv,
        start=start,
        end=end,
        time_column=target_time_column,
    )

    # Sum target columns
    target = sum_columns(
        lf_df,
        config["target_types_present"],
        label=f"{variable}_target",
    ).loc[start:end]

    print(f"   Indicator points: {len(indicator)}")
    print(f"   Target points: {len(target)}")

    # Perform bias detection
    print(f"\n🔬 Running bias detection analysis...")
    result = detect_bias_patterns(
        indicator=indicator,
        target=target,
        variable=variable,
        window_size=window_size,
        step_size=step_size,
        n_clusters=n_clusters,
        changepoint_method=changepoint_method,
        changepoint_threshold=changepoint_threshold,
    )

    # Print summary to console
    print("\n" + "=" * 70)
    print(result.to_summary())
    print("=" * 70)

    # Save recommendations to CSV
    if output_csv:
        output_csv.parent.mkdir(parents=True, exist_ok=True)
        df = result.to_dataframe()
        df.to_csv(output_csv, index=False)
        print(f"\n💾 Recommendations saved to: {output_csv}")
        print(f"   {len(df)} subperiod recommendations written")

    # Save summary to text file
    if output_summary:
        output_summary.parent.mkdir(parents=True, exist_ok=True)
        with open(output_summary, "w") as f:
            f.write(result.to_summary())
            f.write("\n\n")
            f.write("=" * 70 + "\n")
            f.write("DETAILED RECOMMENDATIONS\n")
            f.write("=" * 70 + "\n\n")

            for i, rec in enumerate(result.recommendations, 1):
                f.write(f"{i}. Period: {rec.start.date()} to {rec.end.date()}\n")
                f.write(f"   Method: {rec.recommended_method}\n")
                f.write(f"   Confidence: {rec.confidence:.1%}\n")
                f.write(f"   Reason: {rec.reason}\n")
                f.write(f"   Expected improvements:\n")
                for metric, value in rec.expected_improvement.items():
                    f.write(f"     - {metric}: {value:.1f}%\n")
                if rec.cluster_id is not None:
                    f.write(f"   Cluster ID: {rec.cluster_id}\n")
                f.write("\n")

        print(f"💾 Summary report saved to: {output_summary}")

    # Generate visualizations
    if output_plot:
        print(f"\n📊 Generating bias detection overview plot...")
        plot_bias_detection_overview(result, output_path=output_plot)

    if output_clusters_plot and result.clusters:
        print(f"📊 Generating cluster characteristics plot...")
        plot_cluster_characteristics(result, output_path=output_clusters_plot)

    if output_timeline_plot and result.recommendations:
        print(f"📊 Generating recommendation timeline plot...")
        plot_recommendation_timeline(result, output_path=output_timeline_plot)

    # Print cluster information
    if result.clusters:
        print(f"\n📊 Identified {len(result.clusters)} distinct bias patterns:")
        for cluster in result.clusters:
            print(f"\n   Cluster {cluster.cluster_id}:")
            print(f"     - Periods: {cluster.n_periods}")
            print(f"     - Mean bias: {cluster.mean_bias_pct:+.2f}%")
            print(f"     - Mean MAE: {cluster.mean_mae:.4f}")
            print(f"     - Recommended method: {cluster.recommended_method}")
            print(f"     - Confidence: {cluster.confidence:.1%}")

    # Print changepoint information
    if result.changepoints:
        print(f"\n⚡ Detected {len(result.changepoints)} changepoints:")
        for i, cp in enumerate(result.changepoints[:5], 1):  # Show first 5
            print(
                f"   {i}. {cp.timestamp.date()}: {cp.metric_changed} changed by {cp.change_magnitude:.2f}"
            )
            print(f"      Before: {cp.value_before:.2f}, After: {cp.value_after:.2f}")
        if len(result.changepoints) > 5:
            print(f"   ... and {len(result.changepoints) - 5} more")

    print(f"\n✅ Analysis complete!")
