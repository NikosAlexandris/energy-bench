from pathlib import Path

import pandas as pd
from pandas import Timestamp
from tempdisagg import TempDisaggModel

from energybench.helpers import prepare_dataframe
from energybench.read import read_csv
from energybench.variables import get_variable_config


pd.options.mode.copy_on_write = True  # faster pandas
pd.options.future.infer_string = True


def _sum_columns(
        df: pd.DataFrame,
        columns: list[str],
        series_name: str,
) -> pd.Series:
    """
    """
    missing = [col for col in columns if col not in df.columns]
    if missing:
        raise ValueError(f"Missing columns for '{series_name}': {missing}")

    out = df[columns].sum(axis=1)
    out.name = series_name

    return out


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
) -> Path:
    """
    """
    cfg = get_variable_config(variable)
    output_dir.mkdir(parents=True, exist_ok=True)

    low_frequency_series = read_csv(
        source=low_frequency_csv,
        start=start.normalize(),
        end=end.normalize(),
        time_column=low_frequency_datetime_column,
    )
    low_frequency_series = low_frequency_series.loc[start.normalize():end.normalize()]
    low_frequency_target = _sum_columns(low_frequency_series, cfg["target_columns"], "target")

    high_frequency_series = read_csv(
        source=high_frequency_csv,
        start=start,
        end=end,
        time_column=high_frequency_datetime_column,
    )
    high_frequency_indicator = _sum_columns(high_frequency_series, cfg["indicator_columns"], "indicator")

    df = prepare_dataframe(
        low_frequency_target=low_frequency_target,
        high_frequency_indicator=high_frequency_indicator,
    )
    model = TempDisaggModel(method=method, conversion=conversion)
    model.fit(df)

    print(model.summary())
    if method == 'ensemble':
        print(
                f"\n Overview :"
                f"\n- Each method is fitted separately"
                f"\n- Error metrics (e.g. MAE) are computed"
                f"\n- Weights are optimized to minimize global error"
                f"\n- Final prediction is a weighted average across models"
                f"\n"
        )

    benchmarked_values = model.predict().flatten()
    hourly_index = pd.date_range(start, periods=len(benchmarked_values), freq="h")

    out = pd.DataFrame({
        "DateTime": hourly_index,
        cfg["original_column"]: high_frequency_indicator.reindex(hourly_index).values,
        cfg["output_column"]: benchmarked_values,
    })
    out["date"] = out["DateTime"].dt.date
    out["hour"] = out["DateTime"].dt.hour
    out["month"] = out["DateTime"].dt.month
    out["source_profile"] = "ENTSO-E"
    out["daily_target_source"] = "SFOE"
    out["variable"] = cfg["label"]
    out["target_columns"] = ", ".join(cfg["target_columns"])
    out["indicator_columns"] = ", ".join(cfg["indicator_columns"])
    out["kind"] = cfg.get("kind", "unknown")

    output_path = output_dir / cfg["output_filename"]
    out.to_csv(output_path, index=False, date_format="%Y-%m-%d %H:%M:%S")

    return output_path
