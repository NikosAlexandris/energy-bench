from cyclopts import App
from energybench.commands.scale.simple import scale_indicator_series
from energybench.commands.scale.advanced import scale_indicator_series_advanced


scale_app = App(
    name="scale",
    help="Scale high-frequency time series by a factor to match a reference low-frequency time series",
)

scale_app.command(
    name="simple",
    help="",
)(scale_indicator_series)
scale_app.command(
    name="advanced",
    help="",
)(scale_indicator_series_advanced)
