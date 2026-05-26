"""
Unified plot interface for comparing any two series.
"""

from pathlib import Path
from typing import Literal
import pandas as pd
from pandas import Timestamp

from energybench.core.plots.difference import plot_series_difference, plot_combined_comparison
from energybench.core.validation import KindOfCSV
from energybench.core.utilities import sum_columns
from energybench.core.metrics import compare_series
from energybench.io.reading import read_csv
from energybench.io.writing import save_figure, build_filename
from energybench.core.configuration import get_variable_config, VARIABLE_ORDER, VARIABLES


SeriesType = Literal["indicator", "adjusted", "target"]


def _load_series(
    series_type: str,
    cfg: dict,
    indicator_csv: Path | None = None,
    adjusted_csv: Path | None = None,
    target_csv: Path | None = None,
    start: Timestamp | None = None,
    end: Timestamp | None = None,
    indicator_time_column: str = "DateTime",
    target_time_column: str = "Date",
    adjusted_time_column: str = "DateTime",
    kind_of_adjusted: KindOfCSV = KindOfCSV.benchmarked,
    indicator_column: str | None = None,
    adjusted_column: str | None = None,
    target_column: str | None = None,
    indicator_factor: float = 1.0,
    adjusted_factor: float = 1.0,
    target_factor: float = 1.0,
) -> pd.Series:
    if series_type == "indicator":
        if indicator_column:
            df = read_csv(indicator_csv, start=start, end=end, time_column=indicator_time_column, columns=[indicator_time_column, indicator_column])
            return df[indicator_column].rename("indicator") * indicator_factor
        df = read_csv(indicator_csv, start=start, end=end, time_column=indicator_time_column)
        return sum_columns(df, cfg["indicator_types_present"], "indicator") * indicator_factor
    if series_type == "adjusted":
        df = pd.read_csv(adjusted_csv, parse_dates=[adjusted_time_column])
        df = df.set_index(adjusted_time_column).loc[start:end]
        if adjusted_column:
            return df[adjusted_column].rename("adjusted") * adjusted_factor
        col_map = {
            KindOfCSV.benchmarked: cfg["benchmarked_column"],
            KindOfCSV.scaled: cfg["scaled_column"],
            KindOfCSV.ukf: cfg["output_column"],
        }
        return df[col_map[kind_of_adjusted]].rename("adjusted") * adjusted_factor
    if target_column:
        df = read_csv(target_csv, start=start.normalize(), end=end.normalize(), time_column=target_time_column, columns=[target_time_column, target_column])
        return df[target_column].rename("target") * target_factor
    df = read_csv(target_csv, start=start.normalize(), end=end.normalize(), time_column=target_time_column)
    return sum_columns(df, cfg["target_types_present"], "target") * target_factor


def _plot_single_variable(
    variable: str,
    series1: SeriesType,
    series2: SeriesType,
    start: Timestamp,
    end: Timestamp,
    indicator_csv: Path | None = None,
    adjusted_csv: Path | None = None,
    target_csv: Path | None = None,
    kind_of_adjusted: KindOfCSV = KindOfCSV.benchmarked,
    output_file: Path | None = None,
    indicator_time_column: str = "DateTime",
    target_time_column: str = "Date",
    adjusted_time_column: str = "DateTime",
    series1_label: str | None = None,
    series2_label: str | None = None,
    xlabel: str = "Time",
    units: str = "GWh",
    quiet: bool = False,
    difference_panel: bool = True,
    rolling_mean: bool = True,
    use_step: bool = True,
    indicator_column: str | None = None,
    adjusted_column: str | None = None,
    target_column: str | None = None,
    indicator_factor: float = 1.0,
    adjusted_factor: float = 1.0,
    target_factor: float = 1.0,
) -> None:
    cfg = get_variable_config(variable)

    if not quiet:
        print(f"📖 Loading {series1} series for {cfg['label']}...")
    s1 = _load_series(series1, cfg, indicator_csv, adjusted_csv, target_csv, start, end,
                      indicator_time_column, target_time_column, adjusted_time_column, kind_of_adjusted,
                      indicator_column, adjusted_column, target_column,
                      indicator_factor, adjusted_factor, target_factor)
    if not quiet:
        print(f"📖 Loading {series2} series for {cfg['label']}...")
    s2 = _load_series(series2, cfg, indicator_csv, adjusted_csv, target_csv, start, end,
                      indicator_time_column, target_time_column, adjusted_time_column, kind_of_adjusted,
                      indicator_column, adjusted_column, target_column,
                      indicator_factor, adjusted_factor, target_factor)

    s1_daily = s1.resample("D").sum()
    s2_daily = s2.resample("D").sum()

    series1_display = series1_label or series1.capitalize()
    series2_display = series2_label or series2.capitalize()

    if not quiet:
        print(f"📊 Generating comparison plot for {cfg['label']}...")
    fig = plot_series_difference(
        benchmarked_series=s1_daily, target_series=s2_daily,
        benchmarked_data_source=series1_display, target_data_source=series2_display,
        electricity_generation_type=cfg["label"], frequency="Daily",
        benchmarked_series_label=series1_display, target_series_label=series2_display,
        units=units, xlabel=xlabel, difference_panel=difference_panel,
        show_rolling_mean=rolling_mean,
        use_step=use_step,
    )

    if output_file is None:
        suffix_map = {
            KindOfCSV.benchmarked: "_benchmarked",
            KindOfCSV.scaled: "_scaled",
            KindOfCSV.ukf: "_ukf",
        }
        suffix = suffix_map[kind_of_adjusted] if "adjusted" in (series1, series2) else ""
        base_name = f"{series1}_vs_{series2}{suffix}"
        filename = build_filename(base_name=base_name, variable=variable, start=start, end=end, suffix=".png")
        output_dir = Path("output")
    else:
        filename = output_file.name
        output_dir = output_file.parent if output_file.is_absolute() else Path("output")

    save_figure(fig=fig, filename=filename, output_dir=output_dir, variable=variable,
                close_after=True, quiet=quiet)


def plot_comparison(
    series1: SeriesType,
    series2: SeriesType,
    variable: str,
    start: Timestamp,
    end: Timestamp,
    indicator_csv: Path | None = None,
    adjusted_csv: Path | None = None,
    target_csv: Path | None = None,
    kind_of_adjusted: KindOfCSV = KindOfCSV.benchmarked,
    output_file: Path | None = None,
    indicator_time_column: str = "DateTime",
    target_time_column: str = "Date",
    adjusted_time_column: str = "DateTime",
    series1_label: str | None = None,
    series2_label: str | None = None,
    xlabel: str = "Time",
    units: str = "GWh",
    quiet: bool = False,
    difference_panel: bool = True,
    combine: bool = False,
    rolling_mean: bool = True,
    indicator_column: str | None = None,
    adjusted_column: str | None = None,
    target_column: str | None = None,
    indicator_factor: float = 1.0,
    adjusted_factor: float = 1.0,
    target_factor: float = 1.0,
) -> None:
    """Plot comparison between any two series.

    Parameters
    ----------
    series1 : str
        First series type: ``indicator``, ``adjusted``, or ``target``.
    series2 : str
        Second series type: ``indicator``, ``adjusted``, or ``target``.
    variable : str
        Energy type (e.g. ``nuclear``, ``water``) or ``all`` for all types.
    start : Timestamp
        Start of analysis period.
    end : Timestamp
        End of analysis period.
    indicator_csv : Path, optional
        Path to indicator CSV.
    adjusted_csv : Path, optional
        Path to adjusted/benchmarked CSV.
    target_csv : Path, optional
        Path to target CSV.
    kind_of_adjusted : KindOfCSV
        Kind of adjusted file (benchmarked, scaled, or ukf).
    output_file : Path, optional
        Custom output file path.
    indicator_time_column : str
        Time column in indicator CSV.
    target_time_column : str
        Time column in target CSV.
    adjusted_time_column : str
        Time column in adjusted CSV.
    series1_label : str, optional
        Display label for series1.
    series2_label : str, optional
        Display label for series2.
    xlabel : str
        X-axis label.
    units : str
        Units for y-axis.
    quiet : bool
        Suppress output messages.
    difference_panel : bool
        Show the difference panel.
    combine : bool
        Combine all variables into a single faceted plot (only with ``--variable all``).
    indicator_column : str, optional
        Override column name for indicator series (bypasses config lookup).
    adjusted_column : str, optional
        Override column name for adjusted series (bypasses config lookup).
    target_column : str, optional
        Override column name for target series (bypasses config lookup).
    indicator_factor : float
        Multiply indicator values by this factor (e.g. 1e-6 for kWh->GWh).
    adjusted_factor : float
        Multiply adjusted values by this factor.
    target_factor : float
        Multiply target values by this factor.
    """
    use_step = series2 == "target"
    if variable == "all":
        if combine:
            if not quiet:
                print("📊 Generating combined faceted plot...")
            series1_display = series1_label or series1.capitalize()
            series2_display = series2_label or series2.capitalize()

            series_data = []
            for var in VARIABLE_ORDER:
                cfg = get_variable_config(var)
                s1 = _load_series(
                    series1,
                    cfg,
                    indicator_csv,
                    adjusted_csv,
                    target_csv,
                    start,
                    end,
                    indicator_time_column,
                    target_time_column,
                    adjusted_time_column,
                    kind_of_adjusted,
                    indicator_column,
                    adjusted_column,
                    target_column,
                    indicator_factor,
                    adjusted_factor,
                    target_factor,
                )
                s2 = _load_series(
                    series2,
                    cfg,
                    indicator_csv,
                    adjusted_csv,
                    target_csv,
                    start,
                    end,
                    indicator_time_column,
                    target_time_column,
                    adjusted_time_column,
                    kind_of_adjusted,
                    indicator_column,
                    adjusted_column,
                    target_column,
                    indicator_factor,
                    adjusted_factor,
                    target_factor,
                )
                series_data.append(
                    (s1.resample("D").sum(), s2.resample("D").sum(), cfg["label"])
                )

            fig = plot_combined_comparison(
                series_data,
                series1_display,
                series2_display,
                units,
                series1_source=series1_label,
                series2_source=series2_label,
                start=start,
                end=end,
                show_rolling_mean=rolling_mean,
                use_step=use_step,
            )

            suffix_map = {
                KindOfCSV.benchmarked: "_benchmarked",
                KindOfCSV.scaled: "_scaled",
                KindOfCSV.ukf: "_ukf",
            }
            suffix = (
                suffix_map[kind_of_adjusted] if "adjusted" in (series1, series2) else ""
            )
            base_name = f"{series1}_vs_{series2}{suffix}_combined"
            filename = build_filename(
                base_name=base_name, variable="all", start=start, end=end, suffix=".png"
            )
            save_figure(
                fig=fig,
                filename=filename,
                output_dir=Path("output"),
                variable=None,
                close_after=True,
                quiet=quiet,
            )
        else:
            for var in VARIABLE_ORDER:
                _plot_single_variable(
                    var,
                    series1,
                    series2,
                    start,
                    end,
                    indicator_csv,
                    adjusted_csv,
                    target_csv,
                    kind_of_adjusted,
                    output_file,
                    indicator_time_column,
                    target_time_column,
                    adjusted_time_column,
                    series1_label,
                    series2_label,
                    xlabel,
                    units,
                    quiet,
                    difference_panel,
                    rolling_mean=rolling_mean,
                    use_step=use_step,
                    indicator_column=indicator_column,
                    adjusted_column=adjusted_column,
                    target_column=target_column,
                    indicator_factor=indicator_factor,
                    adjusted_factor=adjusted_factor,
                    target_factor=target_factor,
                )
    else:
        _plot_single_variable(
            variable,
            series1,
            series2,
            start,
            end,
            indicator_csv,
            adjusted_csv,
            target_csv,
            kind_of_adjusted,
            output_file,
            indicator_time_column,
            target_time_column,
            adjusted_time_column,
            series1_label,
            series2_label,
            xlabel,
            units,
            quiet,
            difference_panel,
            rolling_mean=rolling_mean,
            use_step=use_step,
            indicator_column=indicator_column,
            adjusted_column=adjusted_column,
            target_column=target_column,
            indicator_factor=indicator_factor,
            adjusted_factor=adjusted_factor,
            target_factor=target_factor,
        )


def _find_energy_columns(csv_columns: set[str], exclude_water: bool = True) -> dict[str, list[str]]:
    """
    Find which known energy type columns exist in a CSV's columns.

    Returns mapping from variable key to list of matching column names.
    Excludes ``water`` to avoid double-counting (river + storage cover its types).
    """
    result: dict[str, list[str]] = {}
    for key, cfg in VARIABLES.items():
        if exclude_water and key == "water":
            continue
        candidates = set(cfg.get("target_types", [])) | set(cfg.get("indicator_types", []))
        matches = [c for c in csv_columns if c in candidates]
        if matches:
            result[key] = matches
    return result


def plot_totals_comparison(
    *,
    start: Timestamp,
    end: Timestamp,
    reference_csv: Path,
    reference_column: str,
    reference_factor: float = 1.0,
    reference_time_column: str = "DateTime",
    reference_label: str = "Reference",
    total_label: str = "Total",
    total_csv: Path,
    total_factor: float = 1.0,
    total_time_column: str = "DateTime",
    output_file: Path | None = None,
    quiet: bool = False,
    difference_panel: bool = True,
    rolling_mean: bool = True,
    units: str = "GWh",
    xlabel: str = "Time",
    metrics: bool = False,
):
    """Plot sum of all energy types from a CSV vs a reference series.

    Automatically detects energy type columns in ``total_csv`` from the known
    variable configurations. Doubled types (water) are excluded to avoid
    triple-counting with river + storage.

    Parameters
    ----------
    start : Timestamp
        Start of analysis period.
    end : Timestamp
        End of analysis period.
    reference_csv : Path
        Path to reference CSV (e.g. Swissgrid data).
    reference_column : str
        Column name in reference CSV.
    reference_factor : float, default=1.0
        Multiply reference values by this factor.
    reference_time_column : str, default="DateTime"
        Time column in reference CSV.
    reference_label : str, default="Reference"
        Label for the reference series.
    total_label : str, default="Total"
        Label for the total series.
    total_csv : Path
        Path to CSV containing energy type columns (SFOE, ENTSO-E, or output).
    total_factor : float, default=1.0
        Multiply total values by this factor.
    total_time_column : str, default="DateTime"
        Time column in total CSV.
    output_file : Path, optional
        Custom output file path.
    quiet : bool, default=False
        Suppress output messages.
    difference_panel : bool, default=True
        Show the difference panel.
    rolling_mean : bool, default=True
        Show rolling mean in the difference panel.
    units : str, default="GWh"
        Units for y-axis.
    xlabel : str, default="Time"
        X-axis label.
    """
    df_total = pd.read_csv(total_csv, parse_dates=[total_time_column])
    df_total = df_total.set_index(total_time_column).loc[start:end]

    energy_cols = _find_energy_columns(set(df_total.columns))
    if not energy_cols:
        raise ValueError(
            f"No known energy type columns found in {total_csv}. "
            f"Expected columns matching: target_types or indicator_types "
            f"from variable configs (excluding water)."
        )

    total_series = None
    for var, cols in energy_cols.items():
        s = df_total[cols].sum(axis=1).rename(var)
        if not quiet:
            print(f"  {var}: {', '.join(cols)}")
        if total_series is None:
            total_series = s
        else:
            total_series = total_series.add(s, fill_value=0)

    if total_series is None:
        raise ValueError("No energy type columns found to sum.")

    total_series = total_series * total_factor
    total_series_daily = total_series.resample("D").sum()

    if not quiet:
        print(f"📖 Loaded total from {total_csv}")

    df_ref = pd.read_csv(reference_csv, parse_dates=[reference_time_column])
    df_ref = df_ref.set_index(reference_time_column).loc[start:end]
    ref_daily = df_ref[reference_column].rename("reference") * reference_factor
    ref_daily = ref_daily.resample("D").sum()

    if not quiet:
        print(f"📖 Loaded reference from {reference_csv} [{reference_column}]")
        print(f"📊 Total: {total_series_daily.sum():.1f} {units}")
        print(f"📊 {reference_label}: {ref_daily.sum():.1f} {units}")

    if metrics:
        m = compare_series(ref_daily, total_series_daily)
        bias_pct = (
            (m.mean_a / m.mean_b - 1.0) * 100.0
            if m.mean_b not in (0, None)
            else float("nan")
        )
        print(f"\n{'='*70}")
        print(f"📊 Totals Comparison: {reference_label} vs {total_label}")
        print(f"{'='*70}")
        print(f"Period: {start.date()} to {end.date()}")
        print(f"Days: {len(ref_daily)}")
        print("\nSummary Statistics:")
        print(f"  {reference_label} — Mean: {m.mean_a:.4f} {units}, Std: {m.std_a:.4f} {units}, Sum: {m.sum_a:.2f} {units}")
        print(f"  {total_label} — Mean: {m.mean_b:.4f} {units}, Std: {m.std_b:.4f} {units}, Sum: {m.sum_b:.2f} {units}")
        print("\nError Metrics:")
        print(f"  Mean Absolute Error (MAE): {m.mae:.4f} {units}")
        print(f"  Mean Bias Error (MBE): {m.mbe:+.4f} {units}")
        print(f"  Root Mean Square Error (RMSE): {m.rmse:.4f} {units}")
        print(f"  SMAPE: {m.smape:.2f}%")
        print(f"  Bias: {bias_pct:+.2f}%")
        print("\nCorrelation:")
        print(f"  Pearson: {m.pearson:.4f}")
        print(f"  Spearman: {m.spearman:.4f}")
        print(f"{'='*70}\n")

    use_step = True
    fig = plot_series_difference(
        benchmarked_series=ref_daily,
        target_series=total_series_daily,
        benchmarked_data_source=reference_label,
        target_data_source=total_label,
        electricity_generation_type="Total vs Reference",
        frequency="Daily",
        benchmarked_series_label=reference_label,
        target_series_label=total_label,
        units=units,
        xlabel=xlabel,
        difference_panel=difference_panel,
        show_rolling_mean=rolling_mean,
        use_step=use_step,
        difference_label="Daily difference (Reference − Total)",
    )

    if output_file is None:
        filename = f"total_vs_reference_{start.year}_{end.year}.png"
        output_dir = Path("output")
    else:
        filename = output_file.name
        output_dir = output_file.parent if output_file.is_absolute() else Path("output")

    save_figure(fig=fig, filename=filename, output_dir=output_dir, variable=None,
                close_after=True, quiet=quiet)
