from pathlib import Path
from typing import Any
import yaml
import pandas as pd
from cyclopts import App


app = App(name="assemble")


def _load_component_series(
    comp: dict[str, Any],
    global_start: str,
    global_end: str,
    default_time_column: str = "DateTime",
) -> pd.Series:
    csv_path = Path(comp["csv"])
    time_col = comp.get("time_column", default_time_column)
    col = comp["column"]
    factor = float(comp.get("factor", 1.0))

    df = pd.read_csv(csv_path, parse_dates=[time_col]).set_index(time_col)
    # per-component period override or fall back to global
    start = comp.get("start", global_start)
    end = comp.get("end", global_end)
    s = df[col].loc[start:end] * factor
    s.name = comp["name"]
    return s


def assemble_total_from_config(config_path: Path) -> pd.DataFrame:
    with open(config_path, "r") as f:
        cfg = yaml.safe_load(f)

    global_start = cfg["start"]
    global_end = cfg["end"]
    time_column = cfg.get("time_column", "DateTime")

    series_list: list[pd.Series] = []
    for comp in cfg["components"]:
        s = _load_component_series(comp, global_start, global_end, default_time_column=time_column)
        series_list.append(s)

    df = pd.concat(series_list, axis=1).sort_index()
    df["Total"] = df.sum(axis=1)
    df.attrs["total_name"] = cfg.get("total_name", "Total_Production_GWh")
    return df


@app.command()
def assemble_total(
    config: Path,
    output_csv: Path = Path("total_production.csv"),
):
    """
    Assemble total production from component hourly series
    described in a YAML config.
    """
    df = assemble_total_from_config(config)
    df.to_csv(output_csv)
    print(f"Wrote total production to {output_csv}")
