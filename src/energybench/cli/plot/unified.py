"""
Unified plot interface for comparing any two series.
"""

from pathlib import Path
from typing import Literal
import pandas as pd
from pandas import Timestamp

from energybench.core.plots.difference import plot_series_difference
from energybench.core.validation import KindOfCSV
from energybench.core.utilities import sum_columns
from energybench.io.reading import read_csv
from energybench.io.writing import save_figure, build_filename
from energybench.core.configuration import get_variable_config


SeriesType = Literal["indicator", "adjusted", "target"]


def plot_comparison(
    series1: SeriesType,
    series2: SeriesType,
    variable: str,
    start: Timestamp,
    end: Timestamp,
    # File paths (only required ones needed based on series1/series2)
    indicator_csv: Path | None = None,
    adjusted_csv: Path | None = None,
    target_csv: Path | None = None,
    # Optional parameters
    kind_of_adjusted: KindOfCSV = KindOfCSV.benchmarked,
    output_file: Path | None = None,
    indicator_time_column: str = "DateTime",
    target_time_column: str = "Date",
    adjusted_time_column: str = "DateTime",
    series1_label: str | None = None,
    series2_label: str | None = None,
    xlabel: str = "Time",
    units: str = "GWh",
) -> None:
    """
    Plot comparison between any two series: indicator, adjusted, or target.

    Valid combinations:
    - indicator vs target: Shows why adjustment is needed
    - indicator vs adjusted: Shows what changed during adjustment
    - adjusted vs target: Validates adjustment worked correctly

    Parameters
    ----------
    series1 : {"indicator", "adjusted", "target"}
        First series to plot.
    series2 : {"indicator", "adjusted", "target"}
        Second series to plot.
    variable : str
        Energy type (e.g., "river", "nuclear", "solar").
    start : pd.Timestamp
        Start timestamp for plot period.
    end : pd.Timestamp
        End timestamp for plot period.
    indicator_csv : Path, optional
        Path to indicator CSV file. Required if series1 or series2 is "indicator".
    adjusted_csv : Path, optional
        Path to adjusted CSV file. Required if series1 or series2 is "adjusted".
    target_csv : Path, optional
        Path to target CSV file. Required if series1 or series2 is "target".
    kind_of_adjusted : KindOfCSV, default=KindOfCSV.benchmarked
        Type of adjusted series to use (benchmarked, scaled, or scaled-per-day).
    output_file : Path, optional
        Path to save plot. If None, uses default naming convention.
    indicator_time_column : str, default="DateTime"
        Name of datetime column in indicator CSV.
    target_time_column : str, default="Date"
        Name of datetime column in target CSV.
    adjusted_time_column : str, default="DateTime"
        Name of datetime column in adjusted CSV.
    series1_label : str, optional
        Custom label for series1. If None, defaults to series type name.
    series2_label : str, optional
        Custom label for series2. If None, defaults to series type name.
    xlabel : str, default="Time"
        Label for X-axis.
    units : str, default="GWh"
        Units for Y-axis label.

    Raises
    ------
    ValueError
        If series1 equals series2, or if required CSV files are not provided.

    Examples
    --------
    Plot indicator vs target to show why adjustment is needed:

    >>> plot_comparison(
    ...     series1="indicator",
    ...     series2="target",
    ...     variable="river",
    ...     indicator_csv=Path("data/entsoe.csv"),
    ...     target_csv=Path("data/sfoe.csv"),
    ...     start=pd.Timestamp("2024-01-01"),
    ...     end=pd.Timestamp("2024-12-31"),
    ... )

    Plot indicator vs adjusted to show what changed:

    >>> plot_comparison(
    ...     series1="indicator",
    ...     series2="adjusted",
    ...     variable="river",
    ...     indicator_csv=Path("data/entsoe.csv"),
    ...     adjusted_csv=Path("output/river_benchmarked.csv"),
    ...     start=pd.Timestamp("2024-01-01"),
    ...     end=pd.Timestamp("2024-12-31"),
    ... )
    """
    # Validate inputs
    if series1 == series2:
        raise ValueError(f"Cannot plot series against itself: {series1}")
    
    # Check required files are provided
    required_files = {
        "indicator": ("indicator_csv", indicator_csv),
        "adjusted": ("adjusted_csv", adjusted_csv),
        "target": ("target_csv", target_csv),
    }
    
    for series_name in [series1, series2]:
        param_name, param_value = required_files[series_name]
        if param_value is None:
            raise ValueError(
                f"--{param_name.replace('_', '-')} is required when plotting '{series_name}'"
            )
    
    # Get variable configuration
    cfg = get_variable_config(variable)
    
    # Load series based on type
    def load_series(series_type: str) -> pd.Series:
        if series_type == "indicator":
            df = read_csv(
                indicator_csv,
                start=start,
                end=end,
                time_column=indicator_time_column,
            )
            return sum_columns(
                df,
                cfg["indicator_types_present"],
                "indicator",
            )
        
        elif series_type == "adjusted":
            df = pd.read_csv(
                adjusted_csv,
                parse_dates=[adjusted_time_column],
            )
            df = df.set_index(adjusted_time_column).loc[start:end]
            
            # Get the appropriate column based on kind_of_adjusted
            col_map = {
                KindOfCSV.benchmarked: cfg["benchmarked_column"],
                KindOfCSV.scaled: cfg["scaled_column"],
                KindOfCSV.scaled_per_day: cfg["scaled_advanced_column"],
            }
            col = col_map[kind_of_adjusted]
            return df[col].rename("adjusted")
        
        elif series_type == "target":
            df = read_csv(
                target_csv,
                start=start.normalize(),
                end=end.normalize(),
                time_column=target_time_column,
            )
            return sum_columns(
                df,
                cfg["target_types_present"],
                "target",
            )
    
    # Load both series
    print(f"📖 Loading {series1} series...")
    s1 = load_series(series1)
    
    print(f"📖 Loading {series2} series...")
    s2 = load_series(series2)
    
    # Aggregate to daily for plotting
    print(f"📊 Aggregating to daily frequency...")
    s1_daily = s1.resample("D").sum()
    s2_daily = s2.resample("D").sum()
    
    # Set default labels if not provided
    if series1_label is None:
        series1_label = series1.capitalize()
    if series2_label is None:
        series2_label = series2.capitalize()
    
    # Create plot
    print(f"📊 Generating comparison plot...")
    fig = plot_series_difference(
        benchmarked_series=s1_daily,
        target_series=s2_daily,
        benchmarked_data_source=series1_label,
        target_data_source=series2_label,
        electricity_generation_type=cfg["label"],
        frequency="Daily",
        benchmarked_series_label=series1_label,
        target_series_label=series2_label,
        units=units,
        xlabel=xlabel,
    )
    
    # Determine output filename
    if output_file is None:
        filename = build_filename(
            base_name=f"{series1}_vs_{series2}",
            variable=variable,
            start=start,
            end=end,
            suffix=".png",
        )
        output_dir = Path("output")
    else:
        filename = output_file.name
        output_dir = output_file.parent if output_file.is_absolute() else Path("output")
    
    # Save plot
    save_figure(
        fig=fig,
        filename=filename,
        output_dir=output_dir,
        variable=variable,
        close_after=True,
    )
    
    print(f"✅ Plot saved to: {output_dir / variable / filename}")
