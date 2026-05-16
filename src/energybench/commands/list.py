from cyclopts import App
from energybench.variables import VARIABLES
from rich.console import Console
from rich.table import Table


app = App(name="list", help="List electricity generation types and their correspondence between SFOE & ENTSO-E")
console = Console()


@app.command(name="types")
def list_types() -> None:
    table = Table(
        title="Electricity generation types",
        show_header=True,
        header_style="bold",
        box=None,
        show_lines=False,
        pad_edge=False,
    )
    table.add_column("Type", style="bold", no_wrap=True)
    table.add_column("SFOE", style="cyan")
    table.add_column("ENTSO-E", style="green")

    for key, cfg in VARIABLES.items():
        table.add_row(
            key,
            ", ".join(cfg["sfoe_types"]),
            ", ".join(cfg["entsoe_types"]),
        )

    console.print(table)
