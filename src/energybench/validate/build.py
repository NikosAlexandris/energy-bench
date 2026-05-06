from pathlib import Path
import pandas as pd


def save_validation_table(check: pd.DataFrame, output_csv: Path) -> None:
    output_csv.parent.mkdir(parents=True, exist_ok=True)
    check.to_csv(output_csv, index=True)
    print(f"Validation table written to {output_csv}")


def build_target_series(
    low_frequency_csv: Path,
    start: pd.Timestamp,
    end: pd.Timestamp,
    low_frequency_date_column: str = "Date",
    low_frequency_columns: list[str] | None = None,
    frequency: str = "D",
) -> pd.Series:
    """
    """
    if not low_frequency_columns:
        raise ValueError("low_frequency_columns must contain at least one column name.")

    # Read the low frequency time series, which is our "target" or "reference"
    low_frequency_series = pd.read_csv(
        low_frequency_csv,
        parse_dates=[low_frequency_date_column],
        index_col=low_frequency_date_column,
    )
    low_frequency_series = low_frequency_series.loc[start.normalize():end.normalize()]

    missing = [col for col in low_frequency_columns if col not in low_frequency_series.columns]
    if missing:
        raise ValueError(f"Missing columns in {low_frequency_csv}: {missing}")

    for col in low_frequency_columns:
        low_frequency_series[col] = pd.to_numeric(low_frequency_series[col], errors="coerce")

    # In case multiple low-frequency variables (i.e. electricity generation types) correspond
    # to one or multiple high-frequency variables.
    target = low_frequency_series[low_frequency_columns].sum(axis=1).resample(frequency).sum()
    target.name = "target"

    return target


def build_resampled_series(
    csv_file: Path,
    start: pd.Timestamp,
    end: pd.Timestamp,
    datetime_column: str,
    value_columns: list[str],
    frequency: str = "D",
    series_name: str = "series",
) -> pd.Series:
    """
    """
    df = pd.read_csv(
        csv_file,
        parse_dates=[datetime_column],
        index_col=datetime_column,
    )
    df_slice = df.loc[start:end].copy()

    if df_slice.empty:
        return pd.Series(name=series_name, dtype=float)

    missing = [col for col in value_columns if col not in df_slice.columns]
    if missing:
        raise ValueError(f"Missing columns in {csv_file}: {missing}")

    for col in value_columns:
        df_slice[col] = pd.to_numeric(df_slice[col], errors="coerce")

    series = df_slice[value_columns].sum(axis=1).resample(frequency).sum()
    series.name = series_name

    return series


def build_validation_table(
    benchmark_csv: Path,
    high_frequency_csv: Path,
    low_frequency_csv: Path,
    start: pd.Timestamp,
    end: pd.Timestamp,
    benchmark_value_columns: list[str],
    high_frequency_value_columns: list[str],
    low_frequency_columns: list[str],
    benchmark_datetime_column: str = "DateTime",
    high_frequency_datetime_column: str = "DateTime",
    low_frequency_date_column: str = "Date",
    frequency: str = "D",
) -> pd.DataFrame:
    """
    """
    # Read the high-frequency time series, which is our "indicator" or "" ?
    original = build_resampled_series(
        csv_file=high_frequency_csv,
        start=start,
        end=end,
        datetime_column=high_frequency_datetime_column,
        value_columns=high_frequency_value_columns,
        frequency=frequency,
        series_name="original",
    )

    target = build_target_series(
        low_frequency_csv=low_frequency_csv,
        start=start.normalize(),
        end=end.normalize(),
        low_frequency_date_column=low_frequency_date_column,
        low_frequency_columns=low_frequency_columns,
        frequency=frequency,
    )

    benchmarked = build_resampled_series(
        csv_file=benchmark_csv,
        start=start,
        end=end,
        datetime_column=benchmark_datetime_column,
        value_columns=benchmark_value_columns,
        frequency=frequency,
        series_name="benchmarked",
    )

    common_index = original.index.union(target.index).union(benchmarked.index).sort_values()

    original = original.reindex(common_index)
    target = target.reindex(common_index)
    benchmarked = benchmarked.reindex(common_index)

    check = pd.DataFrame(
        {
            "original": original,
            "target": target,
            "benchmarked": benchmarked,
        }
    )

    check["original_minus_target"] = check["original"] - check["target"]
    check["benchmarked_minus_original"] = check["benchmarked"] - check["original"]
    check["benchmarked_minus_target"] = check["benchmarked"] - check["target"]

    return check
