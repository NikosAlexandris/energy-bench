from __future__ import annotations
from pathlib import Path
from pandas import Timestamp
from energybench.compare.types_ import compare_series_types
from energybench.variables import Variable
from energybench.io.writing import save_dataframe


def compare_types(
    variable: Variable,
    high_frequency_csv: Path,
    low_frequency_csv: Path,
    start: Timestamp,
    end: Timestamp,
    output_csv: Path | None = None,
    high_frequency_datetime_column: str = "DateTime",
    low_frequency_date_column: str = "Date",
) -> None:
    datafrane = compare_series_types(
        variable=variable,
        high_frequency_csv=high_frequency_csv,
        low_frequency_csv=low_frequency_csv,
        start=start,
        end=end,
        high_frequency_datetime_column=high_frequency_datetime_column,
        low_frequency_date_column=low_frequency_date_column,
    )

    if output_csv:
        save_dataframe(
            df=datafrane,
            filename=output_csv,
            output_dir=output_csv.parent if output_csv.is_absolute() else Path("output"),
            variable=variable,
            index=False,
        )
    else:
        print(datafrane.to_string(index=False))
