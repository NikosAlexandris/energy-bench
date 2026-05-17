from __future__ import annotations
from cyclopts import App
from energybench.commands.compare.unified import compare_series_unified
from energybench.commands.compare.types import compare_types


compare_app = App(
    name="compare",
    help="Compare time series: indicator, adjusted, and target",
)


# Unified interface for comparing any two series
compare_app.command(
    name="series",
    help="Compare any two series: indicator, adjusted, or target",
)(compare_series_unified)

# Specialized command for comparing energy types
compare_app.command(
    name="types",
    help="Compare energy types between indicator and target sources",
)(compare_types)
