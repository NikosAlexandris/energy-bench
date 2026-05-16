from pathlib import Path
from cyclopts import App
from pandas import Timestamp
from energybench.benchmark import benchmark
from energybench.io.output import save_dataframe, build_filename


app = App(help="Benchmark nuclear generation (Kernkraft vs ENTSO-E Nuclear).")


@app.default
def nuclear(
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
    Benchmark nuclear generation.

    Low-frequency target:      SFOE Kernkraft (daily)
    High-frequency indicator:  ENTSO-E Nuclear (hourly)
    """
    variable= 'nuclear'
    benchmarked_dataframe = benchmark(
        variable=variable,
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

    filename = build_filename(
        base_name="hourly_benchmarked",
        variable=variable,
        start=start,
        end=end,
        suffix=".csv",
    )
    
    save_dataframe(
        df=benchmarked_dataframe,
        filename=filename,
        output_dir=output_dir,
        variable=variable,
        index=False,
    )


if __name__ == "__main__":
    app()
