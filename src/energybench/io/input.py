# from devtools import debug
from pathlib import Path
import polars as pl
from pandas import DataFrame, Timestamp


def read_csv(
    source: Path,
    start: Timestamp,
    end: Timestamp,
    time_column: str = "DateTime",
    columns: list[str] | None = None,
) -> DataFrame:
    """
    Read CSV with Polars and return a pandas DataFrame indexed by time_column.
    """
    polars_start = pl.Series([start], dtype=pl.Datetime("ns"))
    polars_end = pl.Series([end], dtype=pl.Datetime("ns"))

    # Scan with optional column filter, `try_parse_dates=True` is critical; handle nulls/empty strings as null
    scan = pl.scan_csv(
        source=source,
        try_parse_dates=True,
        null_values=["-", "NULL", "NA", ""],
    )

    lazy_columns = pl.LazyFrame.collect_schema(scan).names()
    
    # Handle case when columns is None (read all columns)
    if columns is None:
        available_columns = None
        missing_columns = []
    else:
        available_columns = [c for c in columns if c in lazy_columns]
        missing_columns = [c for c in columns if c not in lazy_columns]

        if not available_columns:
            raise ValueError(f"No columns found for {source.name}: {columns}")
        
        if missing_columns:
            print(f"⚠️  Warning: missing columns for {source.name}: {missing_columns}")
            print(f"   Using available: {available_columns}")

    # Filter by time (prunes rows)
    q = scan.filter(pl.col(time_column).is_between(polars_start, polars_end))

    # Select columns if specified (prunes columns)
    if available_columns:
        q = q.select(available_columns)

    # Cast numeric columns to float (exclude time_column), keep missing as NaN
    df = q.collect().with_columns(
        pl.exclude(time_column).cast(pl.Float64, strict=False)
    )

    return df.to_pandas().set_index(time_column)
