# from devtools import debug
from pathlib import Path
import polars as pl
from pandas import DataFrame, Timestamp


def read_csv(
    source: Path,
    start: Timestamp,
    end: Timestamp,
    time_column: str = "DateTime",
) -> DataFrame:
    """
    Read CSV with Polars and return a pandas DataFrame indexed by time_column.
    """
    polars_start = pl.Series([start], dtype=pl.Datetime("ns"))
    polars_end = pl.Series([end], dtype=pl.Datetime("ns"))

    # `try_parse_dates=True` is critical; handle nulls/empty strings as null
    q = (
        pl.scan_csv(
            source=source,
            try_parse_dates=True,
            null_values=["-", "NULL", "NA", ""],
        )
        .filter(pl.col(time_column).is_between(polars_start, polars_end))
    )

    # Cast all generation columns to float; keep missing as NaN
    df = q.collect().with_columns(pl.exclude(time_column).cast(pl.Float64, strict=False))

    # Polars to_pandas preserves NaN correctly
    return df.to_pandas().set_index(time_column)
