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
) -> pd.Series:
    if not low_frequency_columns:
        raise ValueError("low_frequency_columns must contain at least one column name.")

    low_frequency_series = pd.read_csv(
        low_frequency_csv,
        parse_dates=[low_frequency_date_column],
        index_col=low_frequency_date_column,
    )
    low_frequency_series = low_frequency_series.loc[start:end]
    target = low_frequency_series[low_frequency_columns].sum(axis=1)
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
    """ """
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
    """ """
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
        start=start,
        end=end,
        low_frequency_date_column=low_frequency_date_column,
        low_frequency_columns=low_frequency_columns,
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

    common_index = pd.date_range(start.normalize(), end.normalize(), freq=frequency)
    original = original.reindex(common_index).fillna(0)
    target = target.reindex(common_index).ffill().bfill()
    benchmarked = benchmarked.reindex(common_index).fillna(0)

    check = pd.DataFrame(
        {
            "original": original.values,
            "target": target.values,
            "benchmarked": benchmarked.values,
        },
        index=common_index,
    )
    check["original_minus_target"] = check["original"] - check["target"]
    check["benchmarked_minus_original"] = check["benchmarked"] - check["original"]
    check["benchmarked_minus_target"] = check["benchmarked"] - check["target"]

    return check
