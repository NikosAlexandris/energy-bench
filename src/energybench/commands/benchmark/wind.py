from pathlib import Path
from cyclopts import App
from pandas import Timestamp
from energybench.benchmark import benchmark


app = App(help="Benchmark wind generation.")


@app.default
def wind(
    entsoe_csv: Path,
    sfoe_csv: Path,
    start: Timestamp,
    end: Timestamp,
    entsoe_datetime_column: str = "DateTime",
    sfoe_date_column: str = "Date",
    output_dir: Path = Path("output"),
    method: str = "chow-lin",
    conversion: str = "sum",
):
    output_path = benchmark(
        variable="wind",
        entsoe_csv=entsoe_csv,
        sfoe_csv=sfoe_csv,
        start=start,
        end=end,
        entsoe_datetime_column=entsoe_datetime_column,
        sfoe_date_column=sfoe_date_column,
        output_dir=output_dir,
        method=method,
        conversion=conversion,
    )
    print(f"💾 Output written to {output_path}")


if __name__ == "__main__":
    app()
