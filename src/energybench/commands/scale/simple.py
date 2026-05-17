from pathlib import Path
from energybench.io.reading import read_csv
from energybench.variables import get_variable_config
from pandas import DataFrame, Timestamp
from energybench.models.scaling import scale_series
from energybench.io.writing import save_dataframe, build_filename


def scale_indicator_series(
    variable: str,
    indicator_csv: Path,
    target_csv: Path,
    start: Timestamp,
    end: Timestamp,
    indicator_time_column: str = "DateTime",
    target_time_column: str = "Date",
    indicator_source: str | None = None,
    target_source: str | None = None,
    output_dir: Path = Path("output"),
    warn_threshold: float = 10.0,
    min_daily_sum: float = 0.01,
):
    """
    Scale high-frequency indicator series to match low-frequency targets.

    Parameters
    ----------
    variable : str
        Energy type to scale (e.g., "nuclear", "river", "solar").
    indicator_csv : Path
        Path to high-frequency indicator CSV file (e.g., hourly data).
    target_csv : Path
        Path to low-frequency target CSV file (e.g., daily reference data).
    start : pd.Timestamp
        Start timestamp for analysis period.
    end : pd.Timestamp
        End timestamp for analysis period.
    indicator_time_column : str, default="DateTime"
        Name of datetime column in indicator CSV.
    target_time_column : str, default="Date"
        Name of datetime column in target CSV.
    indicator_source : str, optional
        Name of indicator data source (e.g., "ENTSO-E", "Swissgrid").
        If None, uses default from variable configuration.
    target_source : str, optional
        Name of target data source (e.g., "SFOE", "CustomReference").
        If None, uses default from variable configuration.
    output_dir : Path, default=Path("output")
        Directory for output files.
    warn_threshold : float, default=10.0
        Warn if scaling factor exceeds this value.
    min_daily_sum : float, default=0.01
        Skip scaling if daily sum is below this threshold.

    Notes
    -----
    This function applies simple proportional scaling to match daily totals.
    For each day, it calculates a scaling factor and applies it uniformly
    to all hours within that day.
    """
    cfg = get_variable_config(variable)
    output_dir.mkdir(parents=True, exist_ok=True)

    # Get source names (use provided or fall back to defaults from config)
    actual_indicator_source = indicator_source or cfg.get("default_indicator_source", "indicator")
    actual_target_source = target_source or cfg.get("default_target_source", "target")

    target_series = read_csv(
        source=target_csv,
        start=start.normalize(),
        end=end.normalize(),
        time_column=target_time_column,
        columns=[target_time_column] + cfg["target_types_present"],
    ).squeeze()

    indicator_series = read_csv(
        source=indicator_csv,
        start=start,
        end=end,
        time_column=indicator_time_column,
        columns=[indicator_time_column] + cfg["indicator_types_present"],
    ).squeeze()

    scaled_series = scale_series(
        indicator_series=indicator_series,
        target_series=target_series,
        warn_threshold=warn_threshold,
        min_daily_sum=min_daily_sum,
    )
    out = DataFrame(
        {
            "DateTime": scaled_series.index,
            cfg["original_column"]: indicator_series.reindex(scaled_series.index).values,
            cfg["scaled_output_column"]: scaled_series,
        }
    )
    out["date"] = out["DateTime"].dt.date
    out["hour"] = out["DateTime"].dt.hour
    out["month"] = out["DateTime"].dt.month
    out["variable"] = cfg["label"]
    out["indicator_source"] = actual_indicator_source
    out["indicator_type"] = ", ".join(cfg["indicator_type"])
    out["target_source"] = actual_target_source
    out["target_type"] = ", ".join(cfg["target_type"])
    out["kind"] = cfg.get("kind", "unknown")

    filename = build_filename(
        base_name="hourly_scaled",
        variable=variable,
        start=start,
        end=end,
        suffix=".csv",
    )

    save_dataframe(
        df=out,
        filename=filename,
        output_dir=output_dir,
        variable=variable,
        index=False,
    )
