from __future__ import annotations
from cyclopts import App
from energybench.commands.compare.types import compare_types
from energybench.commands.compare.series import compare_series_shape
from energybench.commands.compare.scaled_vs_target import compare_scaled_vs_target


compare_app = App(
    name="compare",
    help="Compare high-frequency (ex. target source) and low-frequency (ex. indicator source) time series",
)


compare_app.command(
    name="types",
    help="Types",
)(compare_types)
compare_app.command(
    name="shape",
    help="Compare shape of time series",
)(compare_series_shape)
compare_app.command(
    name="scaled-vs-target",
    help="",
)(compare_scaled_vs_target)
