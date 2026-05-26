from cyclopts import App
from energybench.cli.scale.scale import scale_indicator_series


scale_app = App(
    name="scale",
    help="Scale high-frequency time series to match low-frequency daily targets",
)

scale_app.default(scale_indicator_series)
