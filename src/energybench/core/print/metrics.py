from rich.console import Console
from rich.table import Table
from rich import box
import pandas as pd
import warnings


warnings.filterwarnings("ignore", message="invalid value encountered in divide")
console = Console()


def print_metrics(title: str, metrics: pd.Series, digits: int = 3) -> None:
    table = Table(
        title=title,
        box=box.SIMPLE_HEAD,
        show_edge=False,
        header_style="bold",
    )
    table.add_column("Metric", style="cyan", no_wrap=True)
    table.add_column("Value", justify="right")

    for key, value in metrics.items():
        if pd.isna(value):
            rendered = "[dim]NA[/dim]"
        elif isinstance(value, (int, float)):
            rendered = f"{value:.{digits}f}"
        else:
            rendered = str(value)
        table.add_row(str(key), rendered)

    console.print(table)
