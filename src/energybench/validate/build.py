from pathlib import Path
import pandas as pd
from enum import Enum


class KindOfCSV(str, Enum):
    benchmarked = "benchmarked"
    scaled = "scaled"
    scaled_per_day = "scaled-per-day"
    reconciled = "reconciled"


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
    """ """
    if not low_frequency_columns:
        raise ValueError("low_frequency_columns must contain at least one column name.")

    # Read the low frequency time series, which is our "target" or "reference"
    low_frequency_series = pd.read_csv(
        low_frequency_csv,
        parse_dates=[low_frequency_date_column],
        index_col=low_frequency_date_column,
    )
    low_frequency_series = low_frequency_series.loc[start.normalize() : end.normalize()]

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
    # required
    csv_to_validate: Path,
    kind_of_csv: KindOfCSV,
    high_frequency_csv: Path | None,
    low_frequency_csv: Path,
    start: pd.Timestamp,
    end: pd.Timestamp,
    # optional
    csv_value_columns: list[str],
    high_frequency_columns: list[str] | None,
    low_frequency_columns: list[str],
    csv_datetime_column: str = "DateTime",
    high_frequency_datetime_column: str = "DateTime",
    low_frequency_date_column: str = "Date",
    frequency: str = "D",
) -> pd.DataFrame:
    """
    Build a validation table comparing:
    - high-frequency source (optional),
    - CSV to validate,
    - low-frequency reference target.
    """
    adjusted = build_resampled_series(
        csv_file=csv_to_validate,
        start=start,
        end=end,
        datetime_column=csv_datetime_column,
        value_columns=csv_value_columns,
        frequency=frequency,
        series_name=kind_of_csv.name,
    )

    target = build_target_series(
        low_frequency_csv=low_frequency_csv,
        start=start.normalize(),
        end=end.normalize(),
        low_frequency_date_column=low_frequency_date_column,
        low_frequency_columns=low_frequency_columns,
        frequency=frequency,
    )

    series_data = {}
    if high_frequency_csv is not None and high_frequency_columns is not None:
        original = build_resampled_series(
            csv_file=high_frequency_csv,
            start=start,
            end=end,
            datetime_column=high_frequency_datetime_column,
            value_columns=high_frequency_columns,
            frequency=frequency,
            series_name="original",
        )
        series_data["original"] = original

    series_data[kind_of_csv.name] = adjusted
    series_data["target"] = target

    common_index = None
    for s in series_data.values():
        common_index = s.index if common_index is None else common_index.union(s.index)
    common_index = common_index.sort_values()

    for key in list(series_data):
        series_data[key] = series_data[key].reindex(common_index)

    check = pd.DataFrame(series_data)
    check.index.name = "DateTime"
    if "original" in check.columns:
        check["original_minus_target"] = check["original"] - check["target"]
        check[f"{kind_of_csv.name}_minus_original"] = check[kind_of_csv.name] - check["original"]
    check[f"{kind_of_csv.name}_minus_target"] = check[kind_of_csv.name] - check["target"]

    return check


def build_before_after_table(
    csv_file: Path,
    start: pd.Timestamp,
    end: pd.Timestamp,
    datetime_column: str,
    original_columns: list[str],
    adjusted_columns: list[str],
) -> pd.DataFrame:
    """ """
    df = pd.read_csv(
        csv_file,
        parse_dates=[datetime_column],
        index_col=datetime_column,
    )
    df = df.loc[start:end].copy()

    missing_original = [c for c in original_columns if c not in df.columns]
    missing_adjusted = [c for c in adjusted_columns if c not in df.columns]

    if missing_original:
        raise ValueError(f"Missing original columns in {csv_file}: {missing_original}")
    if missing_adjusted:
        raise ValueError(f"Missing adjusted columns in {csv_file}: {missing_adjusted}")

    for col in original_columns + adjusted_columns:
        df[col] = pd.to_numeric(df[col], errors="coerce")

    original = df[original_columns].sum(axis=1)
    adjusted = df[adjusted_columns].sum(axis=1)

    out = pd.DataFrame(
        {
            "original": original,
            "adjusted": adjusted,
        }
    )
    out.index.name = datetime_column
    return out
