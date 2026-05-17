from __future__ import annotations
from pathlib import Path
from cyclopts import App
from energybench.core.check.plausibility import plausibility_check


app = App(name="plausibility", help="Physical plausibility checks.")


@app.command(name="check")
def check(
    csv_file: Path,
    datetime_column: str = "DateTime",
    columns: list[str] | None = None,
    ramp_threshold: float | None = None,
    output_csv: Path | None = None,
) -> None:
    df = plausibility_check(
        csv_file=csv_file,
        datetime_column=datetime_column,
        columns=columns,
        ramp_threshold=ramp_threshold,
    )

    if output_csv:
        output_csv.parent.mkdir(parents=True, exist_ok=True)
        df.to_csv(output_csv, index=False)
        print(f"Wrote {output_csv}")
    else:
        print(df.to_string(index=False))
