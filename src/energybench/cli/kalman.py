from pathlib import Path
import sys
from cyclopts import App
from pandas import Timestamp

# Import from experiments directory at project root (outside src/)
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent / "experiments"))
from kalman_demo import kalman_benchmark


app = App(name="kalman", help="Benchmark high-frequency time series via a Kalman-filter")


@app.command(name="kalman")
def kalman(
    variable: str,
    indicator_csv: Path,
    target_csv: Path,
    start: Timestamp,
    end: Timestamp,
    indicator_time_column: str = "DateTime",
    target_time_column: str = "Date",
    process_variance: float = 0.03,
    observation_variance: float = 0.12,
) -> None:
    """
    Benchmark high-frequency time series using Kalman filter.
    
    Args:
        variable: Energy type to benchmark
        indicator_csv: Path to high-frequency indicator CSV
        target_csv: Path to low-frequency target CSV
        start: Start timestamp for analysis period
        end: End timestamp for analysis period
        indicator_time_column: Name of datetime column in indicator CSV
        target_time_column: Name of datetime column in target CSV
        process_variance: Process variance for Kalman filter
        observation_variance: Observation variance for Kalman filter
    """
    hourly_path, validation_path = kalman_benchmark(
        variable=variable,
        high_frequency_csv=indicator_csv,
        low_frequency_csv=target_csv,
        start=start,
        end=end,
        high_frequency_datetime_column=indicator_time_column,
        low_frequency_datetime_column=target_time_column,
        process_variance=process_variance,
        observation_variance=observation_variance,
    )

    print(f"Wrote {hourly_path}")
    print(f"Wrote {validation_path}")
