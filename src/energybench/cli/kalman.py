from pathlib import Path
import sys
from cyclopts import App
from pandas import Timestamp

# Import from experiments directory at project root (outside src/)
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent / "experiments"))
from kalman_demo import kalman_benchmark

from energybench.core.configuration import get_variable_config
from energybench.core.utilities import sum_columns
from energybench.io.reading import read_csv
from energybench.io.writing import save_dataframe, build_filename
from energybench.models.kalman import unscented_kalman_filter
from pandas import DataFrame


app = App(name="kalman", help="Temporal disaggregation via Kalman filtering")


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


@app.command(name="ukf")
def ukf(
    variable: str,
    indicator_csv: Path,
    target_csv: Path,
    start: Timestamp,
    end: Timestamp,
    indicator_time_column: str = "DateTime",
    target_time_column: str = "Date",
    process_noise: float = 0.01,
    obs_noise_daily: float = 0.05,
    alpha: float = 1.0,
    beta: float = 2.0,
    kappa: float = 0.0,
) -> None:
    """
    Temporal disaggregation via 24D Unscented Kalman Filter (log-space).

    The state tracks 24 hourly log-values per day, following the indicator's
    relative changes.  The daily total observation (sum of exponentials) is
    non-linear — handled naturally by the UKF.

    Parameters
    ----------
    variable : str
        Energy type (e.g. ``river``, ``solar``).
    indicator_csv : Path
        Path to hourly indicator CSV.
    target_csv : Path
        Path to daily target CSV.
    start : Timestamp
        Start of analysis period.
    end : Timestamp
        End of analysis period.
    indicator_time_column : str
        Time column in indicator CSV (default: DateTime).
    target_time_column : str
        Time column in target CSV (default: Date).
    process_noise : float
        Std of process noise added to each hourly log-state (default: 0.01).
    obs_noise_daily : float
        Std of daily observation noise in GWh (default: 0.05).
    alpha : float
        UKF sigma-point spread parameter (default: 1.0).
    beta : float
        UKF prior-knowledge parameter (default: 2.0, optimal for Gaussian).
    kappa : float
        UKF secondary scaling parameter (default: 0.0).
    """
    cfg = get_variable_config(variable)

    target_series = sum_columns(
        read_csv(
            source=target_csv,
            start=start.normalize(),
            end=end.normalize(),
            time_column=target_time_column,
            columns=[target_time_column] + cfg["target_types_present"],
        ),
        cfg["target_types_present"],
        "target",
    )

    indicator_series = sum_columns(
        read_csv(
            source=indicator_csv,
            start=start,
            end=end,
            time_column=indicator_time_column,
            columns=[indicator_time_column] + cfg["indicator_types_present"],
        ),
        cfg["indicator_types_present"],
        "indicator",
    )

    result = unscented_kalman_filter(
        indicator_hourly=indicator_series,
        target_daily=target_series,
        alpha=alpha,
        beta=beta,
        kappa=kappa,
        process_noise=process_noise,
        obs_noise=obs_noise_daily,
    )

    out = DataFrame(
        {
            "DateTime": result.index,
            cfg["original_column"]: indicator_series.reindex(result.index).values,
            cfg["output_column"]: result,
        }
    )
    out["date"] = out["DateTime"].dt.date
    out["hour"] = out["DateTime"].dt.hour
    out["month"] = out["DateTime"].dt.month
    out["variable"] = cfg["label"]
    out["indicator_source"] = cfg.get("default_indicator_source", "indicator")
    out["target_source"] = cfg.get("default_target_source", "target")
    out["kind"] = cfg.get("kind", "unknown")

    filename = build_filename(
        base_name="hourly_ukf_disaggregated",
        variable=variable,
        start=start,
        end=end,
        suffix=".csv",
    )

    save_dataframe(
        df=out,
        filename=filename,
        output_dir=Path("output"),
        variable=variable,
        index=False,
    )
