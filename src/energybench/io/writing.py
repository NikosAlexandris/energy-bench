"""
Centralized output saving functions for Energy-Bench.

This module provides consistent output handling across all commands,
ensuring proper directory structure and file naming conventions.
"""

from pathlib import Path
from typing import Any
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.figure import Figure


def _ensure_output_path(
    output_dir: Path,
    variable: str | None,
    filename: str | Path,
) -> Path:
    """
    Construct output path with optional variable subdirectory.

    Creates directory structure: output_dir/{variable}/filename
    If variable is None, uses: output_dir/filename

    Args:
        output_dir: Base output directory (e.g., "output")
        variable: Energy type for subdirectory (e.g., "river", "nuclear")
        filename: Output filename (can include subdirs)

    Returns:
        Full output path with directories created
    """
    filename = Path(filename)

    # Build path with optional variable subdirectory
    if variable:
        full_path = output_dir / variable / filename
    else:
        full_path = output_dir / filename

    # Create parent directories
    full_path.parent.mkdir(parents=True, exist_ok=True)

    return full_path


def save_dataframe(
    df: pd.DataFrame,
    filename: str | Path,
    output_dir: Path = Path("output"),
    variable: str | None = None,
    index: bool = False,
    date_format: str | None = "%Y-%m-%d %H:%M:%S",
    quiet: bool = False,
    **kwargs: Any,
) -> Path:
    """
    Save DataFrame to CSV with consistent formatting.

    Args:
        df: DataFrame to save
        filename: Output filename (e.g., "river_hourly_2025.csv")
        output_dir: Base output directory (default: "output")
        variable: Energy type for subdirectory (e.g., "river")
        index: Whether to write index (default: False)
        date_format: Format for datetime columns (default: ISO-like)
        quiet: Suppress output messages (default: False)
        **kwargs: Additional arguments passed to df.to_csv()

    Returns:
        Path where file was saved
    """
    output_path = _ensure_output_path(output_dir, variable, filename)

    df.to_csv(
        output_path,
        index=index,
        date_format=date_format,
        **kwargs,
    )

    if not quiet:
        print(f"💾 CSV saved to {output_path}")
    return output_path


def save_figure(
    fig: Figure | None = None,
    filename: str | Path = "plot.png",
    output_dir: Path = Path("output"),
    variable: str | None = None,
    dpi: int = 180,
    bbox_inches: str = "tight",
    facecolor: str = "white",
    edgecolor: str = "none",
    pad_inches: float = 0.08,
    close_after: bool = False,
    quiet: bool = False,
    **kwargs: Any,
) -> Path:
    """
    Save matplotlib figure to PNG with consistent formatting.

    Args:
        fig: Figure to save (if None, uses plt.gcf())
        filename: Output filename (e.g., "river_original_vs_target_2025.png")
        output_dir: Base output directory (default: "output")
        variable: Energy type for subdirectory (e.g., "river")
        dpi: Resolution (default: 180)
        bbox_inches: Bounding box (default: "tight")
        facecolor: Background color (default: "white")
        edgecolor: Edge color (default: "none")
        pad_inches: Padding (default: 0.08)
        close_after: Whether to close figure after saving (default: False)
        quiet: Suppress output messages (default: False)
        **kwargs: Additional arguments passed to plt.savefig()

    Returns:
        Path where file was saved
    """
    output_path = _ensure_output_path(output_dir, variable, filename)

    if fig is None:
        fig = plt.gcf()

    fig.savefig(
        output_path,
        dpi=dpi,
        bbox_inches=bbox_inches,
        facecolor=facecolor,
        edgecolor=edgecolor,
        pad_inches=pad_inches,
        **kwargs,
    )

    if close_after:
        plt.close(fig)

    if not quiet:
        print(f"💾 Plot saved to {output_path}")
    return output_path


def save_text(
    content: str,
    filename: str | Path,
    output_dir: Path = Path("output"),
    variable: str | None = None,
    encoding: str = "utf-8",
) -> Path:
    """
    Save text content to file.

    Args:
        content: Text content to save
        filename: Output filename (e.g., "river_summary_2025.txt")
        output_dir: Base output directory (default: "output")
        variable: Energy type for subdirectory (e.g., "river")
        encoding: Text encoding (default: "utf-8")

    Returns:
        Path where file was saved

    Example:
        >>> save_text(
        ...     content="Summary statistics...",
        ...     filename="river_summary_2025.txt",
        ...     variable="river",
        ... )
        Path('output/river/river_summary_2025.txt')
    """
    output_path = _ensure_output_path(output_dir, variable, filename)

    output_path.write_text(content, encoding=encoding)

    print(f"💾 Text saved to {output_path}")
    return output_path


def build_filename(
    base_name: str,
    variable: str | None = None,
    start: pd.Timestamp | None = None,
    end: pd.Timestamp | None = None,
    suffix: str = ".csv",
    include_variable_prefix: bool = True,
) -> str:
    """
    Build standardized filename with optional temporal extent.

    Args:
        base_name: Base filename (e.g., "hourly_benchmarked")
        variable: Energy type (e.g., "river")
        start: Start timestamp
        end: End timestamp
        suffix: File extension (default: ".csv")
        include_variable_prefix: Whether to prefix with variable name

    Returns:
        Formatted filename

    Examples:
        >>> build_filename("hourly_benchmarked", "river",
        ...                pd.Timestamp("2025-01-01"),
        ...                pd.Timestamp("2025-12-31"))
        'river_hourly_benchmarked_2025.csv'

        >>> build_filename("hourly_benchmarked", "river",
        ...                pd.Timestamp("2024-01-01"),
        ...                pd.Timestamp("2025-12-31"))
        'river_hourly_benchmarked_2024_2025.csv'
    """
    parts = []

    # Add variable prefix if requested
    if include_variable_prefix and variable:
        parts.append(variable)

    # Add base name
    parts.append(base_name)

    # Add temporal extent
    if start and end:
        if start.year == end.year:
            parts.append(str(start.year))
        else:
            parts.append(f"{start.year}_{end.year}")
    elif start:
        parts.append(str(start.year))
    elif end:
        parts.append(str(end.year))

    # Join and add suffix
    filename = "_".join(parts)
    if not filename.endswith(suffix):
        filename += suffix

    return filename
