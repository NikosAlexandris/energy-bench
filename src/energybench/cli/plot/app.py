from cyclopts import App
from energybench.cli.plot.unified import plot_comparison
from energybench.cli.plot.metrics import plot_comparison_metrics
from energybench.cli.plot.assemble import plot_assembled


plot_app = App(
    name="plot",
    help="Plot comparisons between indicator, adjusted, and target series",
)

# Unified interface for plotting comparisons
plot_app.command(
    name="compare",
    help="Plot comparison between any two series: indicator, adjusted, or target",
)(plot_comparison)

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
