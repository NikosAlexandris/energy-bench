from cyclopts import App
from energybench.commands.plot.original_vs_target import plot_original_vs_target
from energybench.commands.plot.difference import plot_difference
from energybench.commands.plot.before_vs_after import plot_before_vs_after
from energybench.commands.plot.metrics import plot_comparison_metrics
from energybench.commands.plot.assemble import plot_assembled


plot_app = App(name="plot", help="Plot original, target and adjusted time series with a context")
plot_app.command(name="original-vs-target")(plot_original_vs_target)
plot_app.command(name="before-vs-after")(plot_before_vs_after)
plot_app.command(name="after-vs-target")(plot_difference)
plot_app.command(name="metrics")(plot_comparison_metrics)
plot_app.command(name="assembled")(plot_assembled)


if __name__ == "__main__":
    plot_app()
