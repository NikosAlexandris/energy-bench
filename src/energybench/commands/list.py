from cyclopts import App
from energybench.variables import VARIABLES


app = App(name="list", help="List available values and mappings.")


@app.command(name="types")
def list_types() -> None:
    for key, cfg in VARIABLES.items():
        print(f"{key}")
        print(f"  SFOE:   {', '.join(cfg['low_frequency_columns'])}")
        print(f"  ENTSO-E: {', '.join(cfg['high_frequency_value_columns'])}")
        print()
