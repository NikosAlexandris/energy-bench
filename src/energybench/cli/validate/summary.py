from pathlib import Path
from pandas import Timestamp
from energybench.core.validation import KindOfCSV, build_validation_table
from energybench.core.configuration import get_variable_config
from energybench.io.writing import save_dataframe


def summary(
    csv_to_validate: Path,
    kind_of_csv: KindOfCSV,
    indicator_csv: Path,
    target_csv: Path,
    start: Timestamp,
    end: Timestamp,
    variable: str,
    csv_time_column: str = "DateTime",
    indicator_time_column: str = "DateTime",
    target_time_column: str = "Date",
    frequency: str = "D",
    output_csv: Path = Path("output/validation_summary.csv"),
):
    """
    Generate validation summary comparing processed CSV against indicator and target data.
    
    Args:
        csv_to_validate: Path to CSV file to validate (benchmarked/scaled output)
        kind_of_csv: Type of CSV (benchmarked or scaled)
        indicator_csv: Path to high-frequency indicator CSV
        target_csv: Path to low-frequency target CSV
        start: Start timestamp for validation period
        end: End timestamp for validation period
        variable: Energy type to validate
        csv_time_column: Name of datetime column in CSV to validate
        indicator_time_column: Name of datetime column in indicator CSV
        target_time_column: Name of datetime column in target CSV
        frequency: Aggregation frequency for validation (default: "D" for daily)
        output_csv: Path to save validation summary
    """
    cfg = get_variable_config(variable)

    kind_of_value_column = {
        "benchmarked": cfg["benchmarked_column"],
        "scaled": cfg["scaled_column"],
    }

    if kind_of_csv not in kind_of_value_column:
        raise ValueError(
            f"Unknown result_kind={kind_of_csv!r}. "
            f"Expected one of: {', '.join(kind_of_value_column)}"
        )
    csv_value_columns = kind_of_value_column[kind_of_csv.value]

    check = build_validation_table(
        csv_to_validate=csv_to_validate,
        kind_of_csv=kind_of_csv,
        high_frequency_csv=indicator_csv,
        low_frequency_csv=target_csv,
        start=start,
        end=end,
        csv_value_columns=csv_value_columns,
        high_frequency_columns=cfg["indicator_types"],
        low_frequency_columns=cfg["target_types"],
        csv_datetime_column=csv_time_column,
        high_frequency_datetime_column=indicator_time_column,
        low_frequency_date_column=target_time_column,
        frequency=frequency,
    )

    # print(check.round(6).to_string())
    save_dataframe(
        df=check,
        filename=output_csv,
        output_dir=output_csv.parent if output_csv.is_absolute() else Path("output"),
        variable=variable,
        index=True,
    )
