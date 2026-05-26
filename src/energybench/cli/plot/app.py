from cyclopts import App
from energybench.cli.plot.unified import plot_comparison, plot_totals_comparison
from energybench.cli.plot.metrics import plot_comparison_metrics
from energybench.cli.plot.assemble import plot_assembled


plot_app = App(
    name="plot",
    help="Plot comparisons between indicator, adjusted, and target series",
)

# Nested sub-app for "compare" with default command and totals subcommand
compare_app = App(name="compare", help="Plot comparison between any two series")
compare_app.default(plot_comparison)
compare_app.command(
    name="totals",
    help="Plot sum of all energy types vs a reference series (e.g. Swissgrid)",
)(plot_totals_comparison)

plot_app.command(compare_app)

# Specialized plot commands
plot_app.command(
    name="metrics",
    help="Plot comparison metrics from CSV file",
)(plot_comparison_metrics)

plot_app.command(
    name="assembled",
    help="Plot assembled multi-variable series",
)(plot_assembled)


if __name__ == "__main__":
    plot_app()
