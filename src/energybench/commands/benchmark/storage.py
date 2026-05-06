from pathlib import Path
from cyclopts import App
from pandas import Timestamp
from energybench.benchmark import benchmark


app = App(help="Benchmark Speicherkraft (reservoir) vs ENTSO-E Hydro Water Reservoir.")


@app.default()
def storage(
    high_frequency_csv: Path,
    low_frequency_csv: Path,
    start: Timestamp,
    end: Timestamp,
    high_frequency_datetime_column: str = "DateTime",
    low_frequency_datetime_column: str = "Date",
    output_dir: Path = Path("output"),
    method: str = "chow-lin",
    conversion: str = "sum",
):
    """
    Benchmark Speicherkraft (reservoir storage).

    Low-frequency target:      SFOE Speicherkraft (daily)
    High-frequency indicator:  ENTSO-E Hydro Water Reservoir (hourly)
    """
    output_path = benchmark(
        variable="storage",
        high_frequency_csv=high_frequency_csv,
        low_frequency_csv=low_frequency_csv,
        start=start,
        end=end,
        high_frequency_datetime_column=high_frequency_datetime_column,
        low_frequency_datetime_column=low_frequency_datetime_column,
        output_dir=output_dir,
        method=method,
        conversion=conversion,
    )
    print(f"💾 Output written to {output_path}")


if __name__ == "__main__":
    app()
