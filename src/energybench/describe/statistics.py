from __future__ import annotations

from pathlib import Path
import pandas as pd


def describe_wide_csv(
    csv_file: Path,
    datetime_column: str,
    start: pd.Timestamp | None = None,
    end: pd.Timestamp | None = None,
    columns: list[str] | None = None,
) -> pd.DataFrame:
    df = pd.read_csv(csv_file, parse_dates=[datetime_column]).set_index(datetime_column)

    if start is not None:
        df = df.loc[start:]
    if end is not None:
        df = df.loc[:end]

    if columns is None:
        columns = [c for c in df.columns if pd.api.types.is_numeric_dtype(df[c])]
    else:
        columns = [c for c in columns if c in df.columns]

    num = df[columns].apply(pd.to_numeric, errors="coerce")

    out = pd.DataFrame(
        {
            "count": num.count(),
            "sum": num.sum(),
            "mean": num.mean(),
            "median": num.median(),
            "min": num.min(),
            "max": num.max(),
            "std": num.std(),
            "missing": num.isna().sum(),
        }
    )
    out.index.name = "variable"
    return out.reset_index()
