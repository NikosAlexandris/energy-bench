from pathlib import Path
from cyclopts import App
from pandas import Timestamp
from energybench.models.benchmarking import benchmark
from energybench.io.writing import save_dataframe, build_filename


app = App(help="Benchmark wind generation.")


@app.default
def wind(
    indicator_csv: Path,
    target_csv: Path,
    start: Timestamp,
    end: Timestamp,
    indicator_time_column: str = "DateTime",
    target_time_column: str = "Date",
    output_dir: Path = Path("output"),
    method: str = "chow-lin",
    conversion: str = "sum",
):
    """
    Benchmark wind generation using temporal disaggregation.

    Parameters
    ----------
    indicator_csv : Path
        Path to high-frequency indicator CSV (e.g., ENTSO-E hourly data).
    target_csv : Path
        Path to low-frequency target CSV (e.g., SFOE daily data).
    start : pd.Timestamp
        Start timestamp for benchmarking period.
    end : pd.Timestamp
        End timestamp for benchmarking period.
    indicator_time_column : str, default="DateTime"
        Name of datetime column in indicator CSV.
    target_time_column : str, default="Date"
        Name of datetime column in target CSV.
    output_dir : Path, default=Path("output")
        Directory for output files.
    method : str, default="chow-lin"
        Temporal disaggregation method to use.
    conversion : str, default="sum"
        Conversion method for aggregation.

    Notes
    -----
    Reconciles ENTSO-E "Wind Onshore" and "Wind Offshore" (hourly) with
    SFOE "Wind" (daily) using temporal disaggregation.
    """
    variable = "wind"
    benchmarked_dataframe = benchmark(
        variable=variable,
        indicator_csv=indicator_csv,
        target_csv=target_csv,
        start=start,
        end=end,
        indicator_time_column=indicator_time_column,
        target_time_column=target_time_column,
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
