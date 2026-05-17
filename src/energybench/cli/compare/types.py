from __future__ import annotations
from pathlib import Path
from pandas import Timestamp
from energybench.core.compare.types_ import compare_series_types
from energybench.core.configuration import Variable
from energybench.io.writing import save_dataframe


def compare_types(
    variable: Variable,
    indicator_csv: Path,
    target_csv: Path,
    start: Timestamp,
    end: Timestamp,
    output_csv: Path | None = None,
    indicator_time_column: str = "DateTime",
    target_time_column: str = "Date",
) -> None:
    """
    Compare energy types between indicator and target data sources.
    
    Args:
        variable: Energy type to compare
        indicator_csv: Path to high-frequency indicator CSV
        target_csv: Path to low-frequency target CSV
        start: Start timestamp for comparison period
        end: End timestamp for comparison period
        output_csv: Optional path to save comparison results
        indicator_time_column: Name of datetime column in indicator CSV
        target_time_column: Name of datetime column in target CSV
    """
    datafrane = compare_series_types(
        variable=variable,
        high_frequency_csv=indicator_csv,
        low_frequency_csv=target_csv,
        start=start,
        end=end,
        high_frequency_datetime_column=indicator_time_column,
        low_frequency_date_column=target_time_column,
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
