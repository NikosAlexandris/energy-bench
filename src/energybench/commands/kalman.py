from pathlib import Path
from cyclopts import App
from pandas import Timestamp
from energybench.experiments.kalman_demo import kalman_benchmark


app = App(name="kalman", help="Benchmark high-frequency time series via a Kalman-filter")


@app.command(name="kalman")
def kalman(
    variable: str,
    indicator_csv: Path,
    daily_reference_csv: Path,
    start: Timestamp,
    end: Timestamp,
    high_frequency_datetime_column: str = "DateTime",
    low_frequency_datetime_column: str = "Date",
    process_variance: float = 0.03,
    observation_variance: float = 0.12,
) -> None:
    hourly_path, validation_path = kalman_benchmark(
        variable=variable,
        high_frequency_csv=indicator_csv,
        low_frequency_csv=daily_reference_csv,
        start=start,
        end=end,
        high_frequency_datetime_column=high_frequency_datetime_column,
        low_frequency_datetime_column=low_frequency_datetime_column,
        process_variance=process_variance,
        observation_variance=observation_variance,
    )

    print(f"Wrote {hourly_path}")
    print(f"Wrote {validation_path}")
