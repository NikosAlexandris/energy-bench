from pathlib import Path
from cyclopts import App
from pandas import Timestamp
from energybench.models.benchmarking import benchmark
from energybench.variables import get_variable_config
from energybench.io.writing import save_dataframe, build_filename


app = App(help="Benchmark river generation (Flusskraft) vs 'Run-of-river and poundage'.")


@app.default()
def river(
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
    Benchmark Flusskraft (run-of-river).

    Low-frequency target:      target source Flusskraft (daily)
    High-frequency indicator:  indicator source Hydro Run-of-river and poundage (hourly)
    """
    variable = "river"
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
