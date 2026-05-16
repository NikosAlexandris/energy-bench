from pathlib import Path

import pandas as pd
from pandas import DataFrame, Timestamp
from tempdisagg import TempDisaggModel

from energybench.helpers import prepare_dataframe, sum_columns
from energybench.io.input import read_csv
from energybench.variables import get_variable_config


pd.options.mode.copy_on_write = True  # faster pandas
pd.options.future.infer_string = True


def benchmark(
    variable: str,
    high_frequency_csv: Path,
    low_frequency_csv: Path,
    start: Timestamp,
    end: Timestamp,
    high_frequency_datetime_column: str = "DateTime",
    low_frequency_datetime_column: str = "Date",
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

    Args:
        variable: Energy type to benchmark (e.g., "nuclear", "river", "solar")
        high_frequency_csv: Path to high-frequency indicator CSV (hourly data source)
        low_frequency_csv: Path to low-frequency target CSV (daily reference data)
        start: Start timestamp for analysis period
        end: End timestamp for analysis period
        high_frequency_datetime_column: Name of datetime column in indicator CSV
        low_frequency_datetime_column: Name of datetime column in target CSV
        output_dir: Directory for output files
        method: Temporal disaggregation method ("chow-lin", "denton", "ensemble", etc.)
        conversion: Conversion type ("sum" for flow variables, "average" for stock variables)

    Returns:
        DataFrame with benchmarked hourly values and metadata

    Examples:
        >>> # Benchmark nuclear generation with hourly and daily data
        >>> result = benchmark(
        ...     variable="nuclear",
        ...     high_frequency_csv=Path("data/indicator_hourly.csv"),
        ...     low_frequency_csv=Path("data/target_daily.csv"),
        ...     start=pd.Timestamp("2025-01-01"),
        ...     end=pd.Timestamp("2025-12-31"),
        ... )

        >>> # Use ensemble method for better accuracy
        >>> result = benchmark(
        ...     variable="solar",
        ...     high_frequency_csv=Path("data/indicator_hourly.csv"),
        ...     low_frequency_csv=Path("data/target_daily.csv"),
        ...     start=pd.Timestamp("2025-01-01"),
        ...     end=pd.Timestamp("2025-12-31"),
        ...     method="ensemble",
        ... )
    """
    cfg = get_variable_config(variable)
    output_dir.mkdir(parents=True, exist_ok=True)

    # Read low-frequency target data
    target_data = read_csv(
        source=low_frequency_csv,
        start=start.normalize(),
        end=end.normalize(),
        time_column=low_frequency_datetime_column,
        columns=[low_frequency_datetime_column] + cfg["target_types_present"],
    )

    target_series = sum_columns(
        df=target_data, columns=cfg["target_types_present"], output_name="target"
    )

    # Read high-frequency indicator data
    indicator_data = read_csv(
        source=high_frequency_csv,
        start=start,
        end=end,
        time_column=high_frequency_datetime_column,
        columns=[high_frequency_datetime_column] + cfg["indicator_types_present"],
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
    output_dataframe["indicator_source"] = "indicator"
    output_dataframe["indicator_type"] = ", ".join(cfg["indicator_type"])
    output_dataframe["target_source"] = "target"
    output_dataframe["target_type"] = ", ".join(cfg["target_type"])
    output_dataframe["kind"] = cfg.get("kind", "unknown")

    return output_dataframe
