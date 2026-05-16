#!/usr/bin/env python
"""
Swiss electricity benchmarking CLI.
Benchmark, validate, plot, fetch, clean, compare, and check Swiss electricity generation time series.
"""

from cyclopts import App

from energybench.commands.list import app as list_app
from energybench.commands.data import app as data_app
from energybench.commands.compare.app import compare_app
from energybench.commands.describe import app as describe_app
from energybench.commands.plot.app import plot_app
from energybench.commands.scale.app import scale_app
from energybench.commands.benchmark import nuclear, river, solar, storage, thermal, water, wind
from energybench.commands.kalman import app as kalman_app
from energybench.commands.plausibility import app as plausibility_app
from energybench.commands.validate.app import validate_app
from energybench.commands.assemble import app as assemble_app
from energybench.commands.analyse.app import analyse_app

app = App(
    name="energy-bench",
    help="Benchmark, validate, plot, fetch, clean, compare, and check Swiss electricity generation time series",
    help_epilogue="Built for EDIH's Energy-Data Hackathon Challenge #2 : https://www.energydatahackdays.ch/challenges/estimating-hourly-energy-production-for-switzerland",
    version_flags=["--version", "-V"],
)
app.register_install_completion_command()

benchmark_app = App(
    name="benchmark",
    help="Benchmark high-frequency time series using methods of temporal disaggregation",
)
water.app.sort_key = 1
river.app.sort_key = 2
storage.app.sort_key = 3
solar.app.sort_key = 4
wind.app.sort_key = 5
nuclear.app.sort_key = 6
thermal.app.sort_key = 7

benchmark_app.command(water.app, name="water")
benchmark_app.command(nuclear.app, name="nuclear")
benchmark_app.command(river.app, name="river")
benchmark_app.command(storage.app, name="storage")
benchmark_app.command(wind.app, name="wind")
benchmark_app.command(solar.app, name="solar")
benchmark_app.command(thermal.app, name="thermal")

list_app.sort_key = 1
data_app.sort_key = 2
describe_app.sort_key = 3
compare_app.sort_key = 4
plot_app.sort_key = 5
scale_app.sort_key = 6
benchmark_app.sort_key = 7
kalman_app.sort_key = 8
validate_app.sort_key = 9
plausibility_app.sort_key = 10
analyse_app.sort_key = 11

app.command(list_app)
app.command(data_app)
app.command(describe_app)
app.command(compare_app)
app.command(plot_app)
app.command(scale_app)
app.command(benchmark_app)
app.command(kalman_app)
app.command(validate_app)
app.command(plausibility_app)
app.command(assemble_app)
app.command(analyse_app)


def main():
    """Main CLI entrypoint."""
    app()


if __name__ == "__main__":
    main()
