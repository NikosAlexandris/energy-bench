"""
Function to compare adjustment methods.
"""

from pathlib import Path
from typing import Annotated, Optional

import cyclopts
import pandas as pd


def compare_adjustment_methods(
    variable: Annotated[
        str,
        cyclopts.Parameter(help="Energy type to analyze"),
    ],
    indicator_csv: Annotated[
        Path,
        cyclopts.Parameter(help="Path to high-frequency indicator CSV"),
    ],
    target_csv: Annotated[
        Path,
        cyclopts.Parameter(help="Path to low-frequency target CSV"),
    ],
    start: Annotated[
        pd.Timestamp,
        cyclopts.Parameter(help="Start date", converter=pd.Timestamp),
    ],
    end: Annotated[
        pd.Timestamp,
        cyclopts.Parameter(help="End date", converter=pd.Timestamp),
    ],
    methods: Annotated[
        list[str],
        cyclopts.Parameter(help="Methods to compare (scaling, benchmarking, advanced_scaling)"),
    ] = None,
    output_csv: Annotated[
        Optional[Path],
        cyclopts.Parameter(help="Output CSV for comparison results"),
    ] = None,
) -> None:
    """
    Compare different adjustment methods on the same data.
    
    This helps determine which method works best for your specific case.
    
    Example:
        nrgbnc analyze compare-methods river \\
            --indicator-csv data/hourly_indicator.csv \\
            --target-csv data/daily_target.csv \\
            --start 2024-01-01 \\
            --end 2024-12-31 \\
            --methods scaling benchmarking advanced_scaling
    """
    if methods is None:
        methods = ["scaling", "benchmarking", "advanced_scaling"]

    print(f"🔬 Comparing adjustment methods for {variable}...")
    print(f"   Methods: {', '.join(methods)}")
    print(f"   Period: {start.date()} to {end.date()}")

    # TODO: Implement method comparison logic
    # This would run each method and compare their results

    print("\n⚠️  Method comparison not yet fully implemented")
    print("   Use 'nrgbnc analyze bias-patterns' for recommendations")
