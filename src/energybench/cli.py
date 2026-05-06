#!/usr/bin/env python
"""
Swiss electricity benchmarking CLI.
Benchmark, validate, plot, fetch, clean, compare, and check Swiss electricity generation time series.
"""
from cyclopts import App

from energybench.commands.list import app as list_app
from energybench.commands.data import app as data_app
from energybench.commands.compare import app as compare_app
from energybench.commands.describe import app as describe_app
from energybench.commands.plot import app as plot_app
from energybench.commands.benchmark import nuclear, river, solar, storage, thermal, water, wind
from energybench.commands.kalman import app as kalman_app
from energybench.commands.plausibility import app as plausibility_app
from energybench.commands.validate import app as validate_app

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
benchmark_app.command(water.app, name="water")
benchmark_app.command(nuclear.app, name="nuclear")
benchmark_app.command(river.app, name="river")
benchmark_app.command(storage.app, name="storage")
benchmark_app.command(wind.app, name="wind")
benchmark_app.command(solar.app, name="solar")
benchmark_app.command(thermal.app, name="thermal")

app.command(list_app, name="list")
app.command(data_app, name="data")
app.command(describe_app, name="describe")
app.command(compare_app, name="compare")
app.command(plot_app, name="plot")
app.command(benchmark_app, name="benchmark")
app.command(kalman_app, name="kalman")
app.command(validate_app, name="validate")
app.command(plausibility_app, name="plausibility")


def main():
    """Main CLI entrypoint."""
    app()


if __name__ == "__main__":
    main()
