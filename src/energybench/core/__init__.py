"""
Core library modules for Energy-Bench.

This package contains reusable library functions organized by domain:
- plots: Visualization functions
- compare: Metrics and comparison utilities
- validate: Validation and quality checks
- metrics.py: Core metrics calculations (moved from compare/)
- shape.py: Shape comparison utilities (moved from compare/)
- validation.py: Validation utilities (moved from validate/)
"""

# Re-export commonly used functions for convenience
# from .metrics import calculate_metrics
# from .shape import compare_shape
# from .validation import build_validation_report
from .plots.before_after import plot_series_before_and_after
from .plots.difference import plot_series_difference
from .plots.metrics import plot_metrics_overview, set_tufte_style
from .plots.fit import plot_daily_fit

__all__ = [
    # Metrics
    # "calculate_metrics",
    # "compare_shape",
    # Validation
    # "build_validation_report",
    # Plotting
    "plot_series_before_and_after",
    "plot_series_difference",
    "plot_metrics_overview",
    "plot_daily_fit",
    "set_tufte_style",
]
