from pathlib import Path

import pandas as pd
from pandas import DataFrame, Timestamp
from tempdisagg import TempDisaggModel

from energybench.helpers import prepare_dataframe, sum_columns
from energybench.io.reading import read_csv
from energybench.variables import get_variable_config


pd.options.mode.copy_on_write = True  # faster pandas
pd.options.future.infer_string = True


def benchmark(
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
    method: str = "chow-lin",
    conversion: str = "sum",
) -> DataFrame:
    """
    Benchmark high-frequency indicator series using temporal disaggregation.

    This function reconciles high-frequency time series data with low-frequency
    target values using temporal disaggregation methods. It ensures that the
    high-frequency estimates sum to match the low-frequency totals while
    preserving temporal patterns from the indicator series.

    The function is source-agnostic and works with any time series data sources.

    Parameters
    ----------
    variable : str
        Energy type to benchmark (e.g., "nuclear", "river", "solar").
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
    method : str, default="chow-lin"
        Temporal disaggregation method. Options: "chow-lin", "denton",
        "ensemble", etc.
    conversion : str, default="sum"
        Conversion type: "sum" for flow variables, "average" for stock variables.

    Returns
    -------
    pd.DataFrame
        DataFrame with benchmarked hourly values and metadata columns including:
        DateTime, original values, benchmarked values, date, hour, month,
        variable, indicator_source, indicator_type, target_source, target_type, kind.

    Examples
    --------
    Benchmark nuclear generation with ENTSO-E hourly and SFOE daily data:

    >>> result = benchmark(
    ...     variable="nuclear",
    ...     indicator_csv=Path("data/entsoe_hourly.csv"),
    ...     target_csv=Path("data/sfoe_daily.csv"),
    ...     start=pd.Timestamp("2025-01-01"),
    ...     end=pd.Timestamp("2025-12-31"),
    ... )

    Use custom data sources with explicit source tracking:

    >>> result = benchmark(
    ...     variable="solar",
    ...     indicator_csv=Path("data/swissgrid_15min.csv"),
    ...     target_csv=Path("data/custom_daily.csv"),
    ...     start=pd.Timestamp("2025-01-01"),
    ...     end=pd.Timestamp("2025-12-31"),
    ...     indicator_source="Swissgrid",
    ...     target_source="CustomReference",
    ...     method="ensemble",
    ... )
    """
    cfg = get_variable_config(variable)
    output_dir.mkdir(parents=True, exist_ok=True)

    # Get source names (use provided or fall back to defaults from config)
    actual_indicator_source = indicator_source or cfg.get("default_indicator_source", "indicator")
    actual_target_source = target_source or cfg.get("default_target_source", "target")

    # Read low-frequency target data
    target_data = read_csv(
        source=target_csv,
        start=start.normalize(),
        end=end.normalize(),
        time_column=target_time_column,
        columns=[target_time_column] + cfg["target_types_present"],
    )

    target_series = sum_columns(
        df=target_data, columns=cfg["target_types_present"], output_name="target"
    )

    # Read high-frequency indicator data
    indicator_data = read_csv(
        source=indicator_csv,
        start=start,
        end=end,
        time_column=indicator_time_column,
        columns=[indicator_time_column] + cfg["indicator_types_present"],
    )

    indicator_series = sum_columns(
        df=indicator_data, columns=cfg["indicator_types_present"], output_name="indicator"
    )

    # Prepare data for temporal disaggregation
    df = prepare_dataframe(
        target_series=target_series,
        indicator_series=indicator_series,
    )
    model = TempDisaggModel(method=method, conversion=conversion)
    model.fit(df)

    print(model.summary())
    if method == "ensemble":
        print(
            "\n Overview :"
            "\n- Each method is fitted separately"
            "\n- Error metrics (e.g. MAE) are computed"
            "\n- Weights are optimized to minimize global error"
            "\n- Final prediction is a weighted average across models"
            "\n"
        )

    benchmarked_values = model.predict().flatten()
    hourly_index = pd.date_range(start, periods=len(benchmarked_values), freq="h")

    output_dataframe = pd.DataFrame(
        {
            "DateTime": hourly_index,
            cfg["original_column"]: indicator_series.reindex(hourly_index).values,
            cfg["output_column"]: benchmarked_values,
        }
    )
    output_dataframe["date"] = output_dataframe["DateTime"].dt.date
    output_dataframe["hour"] = output_dataframe["DateTime"].dt.hour
    output_dataframe["month"] = output_dataframe["DateTime"].dt.month
    output_dataframe["variable"] = cfg["label"]
    output_dataframe["indicator_source"] = actual_indicator_source
    output_dataframe["indicator_type"] = ", ".join(cfg["indicator_type"])
    output_dataframe["target_source"] = actual_target_source
    output_dataframe["target_type"] = ", ".join(cfg["target_type"])
    output_dataframe["kind"] = cfg.get("kind", "unknown")

    return output_dataframe
