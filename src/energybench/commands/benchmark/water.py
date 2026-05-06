from pathlib import Path
from cyclopts import App
from pandas import Timestamp
from energybench.benchmark import benchmark


app = App(help="Benchmark hydro (Flusskraft + Speicherkraft vs ENTSO-E hydro total).")


@app.default()
def water(
    high_frequency_csv: Path,
    low_frequency_csv: Path,
    start: Timestamp,
    end: Timestamp,
    high_frequency_datetime_column: str = "DateTime",
    low_frequency_datetime_column: str = "Date",
    output_dir: Path = Path("output"),
    method: str = "chow-lin",
    conversion: str = "sum",
) -> None:
    """
    Benchmark hydro generation.

    Parameters
    ----------
    high_frequency_csv: Path
        ENTSO-E CSV time series for electricity generation

    low_frequency_csv:
        SFOE CSV time series for electricity generation

    start: str
        The start timestamp string

    end: str
        The end timestamp string

    Notes
    -----
    Low-frequency target:      SFOE Flusskraft + Speicherkraft (daily)
    High-frequency indicator:  ENTSO-E Run-of-river + Reservoir + Pumped Storage (hourly)
    """
    output_path = benchmark(
        variable="water",
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
