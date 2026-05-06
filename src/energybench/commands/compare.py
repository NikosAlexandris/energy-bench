from __future__ import annotations

from pathlib import Path
import pandas as pd
from cyclopts import App

from energybench.compare.types import compare_types
from energybench.variables import Variable


app = App(name="compare", help="Compare SFOE and ENTSO-E series.")


@app.command(name="types")
def compare_types_command(
    variable: Variable,
    high_frequency_csv: Path,
    low_frequency_csv: Path,
    start: str,
    end: str,
    output_csv: Path | None = None,
    high_frequency_datetime_column: str = "DateTime",
    low_frequency_date_column: str = "Date",
) -> None:
    df = compare_types(
        variable=variable,
        high_frequency_csv=high_frequency_csv,
        low_frequency_csv=low_frequency_csv,
        start=pd.Timestamp(start),
        end=pd.Timestamp(end),
        high_frequency_datetime_column=high_frequency_datetime_column,
        low_frequency_date_column=low_frequency_date_column,
    )

    if output_csv:
        output_csv.parent.mkdir(parents=True, exist_ok=True)
        df.to_csv(output_csv, index=False)
        print(f"Wrote {output_csv}")
    else:
        print(df.to_string(index=False))
