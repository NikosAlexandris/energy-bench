from pathlib import Path
from pandas import Timestamp
from energybench.validate.build import KindOfCSV, build_validation_table
from energybench.variables import get_variable_config
from energybench.io.output import save_dataframe


def summary(
    csv_to_validate: Path,
    kind_of_csv: KindOfCSV,
    high_frequency_csv: Path,
    low_frequency_csv: Path,
    start: Timestamp,
    end: Timestamp,
    variable: str,
    csv_datetime_column: str = "DateTime",
    high_frequency_datetime_column: str = "DateTime",
    low_frequency_date_column: str = "Date",
    frequency: str = "D",
    output_csv: Path = Path("output/validation_summary.csv"),
):
    """
    """
    cfg = get_variable_config(variable)

    kind_of_value_column = {
        "benchmarked": cfg["benchmarked_values"],
        "scaled": cfg["scaled_values"],
        "scaled-per-day": cfg["scaled_per_day_values"],
        # "reconciled": cfg["reconciled_values"],
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
        high_frequency_csv=high_frequency_csv,
        low_frequency_csv=low_frequency_csv,
        start=start,
        end=end,
        csv_value_columns=csv_value_columns,
        high_frequency_columns=cfg["entsoe_types"],
        low_frequency_columns=cfg["sfoe_types"],
        csv_datetime_column=csv_datetime_column,
        high_frequency_datetime_column=high_frequency_datetime_column,
        low_frequency_date_column=low_frequency_date_column,
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
