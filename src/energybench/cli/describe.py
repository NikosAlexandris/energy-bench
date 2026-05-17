from __future__ import annotations
from pathlib import Path
import pandas as pd
from cyclopts import App
from energybench.core.describe.statistics import describe_wide_csv


app = App(name="stats", help="Descriptive statistics.")


@app.command(name="describe")
def describe(
    csv_file: Path,
    datetime_column: str = "DateTime",
    columns: list[str] | None = None,
    start: str | None = None,
    end: str | None = None,
    output_csv: Path | None = None,
) -> None:
    df = describe_wide_csv(
        csv_file=csv_file,
        datetime_column=datetime_column,
        columns=columns,
        start=pd.Timestamp(start) if start else None,
        end=pd.Timestamp(end) if end else None,
    )

    if output_csv:
        output_csv.parent.mkdir(parents=True, exist_ok=True)
        df.to_csv(output_csv, index=False)
        print(f"Wrote {output_csv}")
    else:
        print(df.to_string(index=False))
