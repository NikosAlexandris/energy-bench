from pathlib import Path
from cyclopts import App
from pandas import Timestamp
from energybench.validate.build import build_validation_table, save_validation_table
from energybench.variables import get_variable_config


app = App(help="Validate benchmarked outputs.")


@app.command(name="summary")
def summary(
    benchmark_csv: Path,
    high_frequency_csv: Path,
    low_frequency_csv: Path,
    start: Timestamp,
    end: Timestamp,
    variable: str,
    benchmark_datetime_column: str = "DateTime",
    high_frequency_datetime_column: str = "DateTime",
    low_frequency_date_column: str = "Date",
    frequency: str = "D",
    output_csv: Path = Path("output/validation_summary.csv"),
):
    cfg = get_variable_config(variable)
    check = build_validation_table(
        benchmark_csv=benchmark_csv,
        high_frequency_csv=high_frequency_csv,
        low_frequency_csv=low_frequency_csv,
        start=start,
        end=end,
        benchmark_value_columns=cfg["benchmark_value_columns"],
        high_frequency_value_columns=cfg["high_frequency_value_columns"],
        low_frequency_columns=cfg["low_frequency_columns"],
        benchmark_datetime_column=benchmark_datetime_column,
        high_frequency_datetime_column=high_frequency_datetime_column,
        low_frequency_date_column=low_frequency_date_column,
        frequency=frequency,
    )
    print(check.round(6).to_string())
    save_validation_table(check, output_csv)


@app.command(name="daily-balance")
def daily_balance(
    benchmark_csv: Path,
    low_frequency_csv: Path,
    start: Timestamp,
    end: Timestamp,
    variable: str,
    benchmark_datetime_column: str = "DateTime",
    low_frequency_date_column: str = "Date",
):
    cfg = get_variable_config(variable)
    check = build_validation_table(
        benchmark_csv=benchmark_csv,
        high_frequency_csv=benchmark_csv,
        low_frequency_csv=low_frequency_csv,
        start=start,
        end=end,
        benchmark_value_columns=cfg["benchmark_value_columns"],
        high_frequency_value_columns=cfg["benchmark_value_columns"],
        low_frequency_columns=cfg["low_frequency_columns"],
        benchmark_datetime_column=benchmark_datetime_column,
        high_frequency_datetime_column=benchmark_datetime_column,
        low_frequency_date_column=low_frequency_date_column,
        frequency="D",
    )

    max_abs = check["benchmarked_minus_target"].abs().max()
    print(check[["target", "benchmarked", "benchmarked_minus_target"]].round(6).to_string())
    print(f"\nMax |benchmarked - target|: {max_abs:.10f}")
