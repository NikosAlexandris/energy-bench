from __future__ import annotations

from pathlib import Path
import re
from typing import Iterable

import pandas as pd


DEFAULT_SHEET_NAME = "Zeitreihen0h15"


def iter_excel_files(
    raw_dir: Path | None = None,
    files: Iterable[Path | str] | None = None,
) -> list[Path]:
    if files is not None:
        return sorted(Path(f) for f in files)

    if raw_dir is None:
        raise ValueError("Either raw_dir or files must be provided.")

    return sorted(raw_dir.glob("*.xlsx"))


def normalize_header_value(value) -> str:
    if pd.isna(value):
        return ""
    text = str(value).replace("\n", " ")
    text = re.sub(r"\s+", " ", text).strip()
    return text


def combine_headers(row1, row2) -> list[str]:
    headers: list[str] = []
    used: dict[str, int] = {}

    for h1, h2 in zip(row1, row2):
        a = normalize_header_value(h1)
        b = normalize_header_value(h2)

        if a and b:
            col = f"{a} - {b}"
        elif b:
            col = b
        elif a:
            col = a
        else:
            col = "unnamed"

        count = used.get(col, 0)
        final_col = col if count == 0 else f"{col}__{count + 1}"
        used[col] = count + 1
        headers.append(final_col)

    return headers


def find_timestamp_column(columns: list[str]) -> str:
    candidates = [
        c
        for c in columns
        if "zeitstempel" in c.lower() or "timestamp" in c.lower() or c.lower() == "ds"
    ]
    if not candidates:
        raise ValueError("Could not find a timestamp column.")
    return candidates[0]


def is_production_column(col: str) -> bool:
    c = col.lower()

    production_keywords = [
        "production",
        "produktion",
        "erzeugung",
        "energy production",
        "energieproduktion",
        "stromproduktion",
        "electrical energy produced",
        "fed directly into the transmission system",
        "einspeis",
        "feed-in",
    ]

    exclude_keywords = [
        "verbrauch",
        "consumption",
        "end user",
        "end-user",
        "load",
        "pumps",
        "loss",
        "verluste",
        "import",
        "export",
        "physical import",
        "physical export",
    ]

    has_prod = any(k in c for k in production_keywords)
    has_excl = any(k in c for k in exclude_keywords)
    return has_prod and not has_excl


def load_raw_sheet(file_path: Path, sheet_name: str = DEFAULT_SHEET_NAME) -> pd.DataFrame:
    raw = pd.read_excel(file_path, sheet_name=sheet_name, header=None)
    if raw.shape[0] < 3:
        raise ValueError(
            f"Sheet '{sheet_name}' in '{file_path.name}' does not contain enough rows."
        )
    return raw


def load_and_clean_production_data(
    file_path: Path,
    sheet_name: str = DEFAULT_SHEET_NAME,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    raw = load_raw_sheet(file_path=file_path, sheet_name=sheet_name)

    header_row_1 = raw.iloc[0].tolist()
    header_row_2 = raw.iloc[1].tolist()
    columns = combine_headers(header_row_1, header_row_2)

    df = raw.iloc[2:].copy()
    df.columns = columns

    timestamp_col = find_timestamp_column(df.columns.tolist())
    production_cols = [c for c in df.columns if is_production_column(c)]

    if not production_cols:
        raise ValueError(
            f"No production-related columns found. Inspect merged headers in '{file_path.name}'."
        )

    keep_cols = [timestamp_col] + production_cols
    df = df[keep_cols].copy()
    df = df.rename(columns={timestamp_col: "ds"})

    df["ds"] = pd.to_datetime(
        df["ds"],
        format="%d.%m.%Y %H:%M",
        errors="coerce",
    )

    for col in production_cols:
        df[col] = pd.to_numeric(df[col], errors="coerce")

    df = (
        df.dropna(subset=["ds"])
        .drop_duplicates(subset=["ds"])
        .sort_values("ds")
        .reset_index(drop=True)
    )

    value_cols = [c for c in df.columns if c != "ds"]
    non_empty_cols = [c for c in value_cols if df[c].notna().any()]
    df_wide = df[["ds"] + non_empty_cols].copy()

    df_long = (
        df_wide.melt(id_vars="ds", var_name="variable", value_name="value")
        .dropna(subset=["value"])
        .reset_index(drop=True)
    )

    return df_wide, df_long


def output_paths_for_excel(source_file: Path, clean_dir: Path) -> tuple[Path, Path]:
    stem = source_file.stem
    wide_csv = clean_dir / f"{stem}_production_wide.csv"
    long_csv = clean_dir / f"{stem}_production_long.csv"
    return wide_csv, long_csv


def outputs_exist_for_excel(source_file: Path, clean_dir: Path) -> bool:
    wide_csv, long_csv = output_paths_for_excel(source_file, clean_dir)
    return wide_csv.exists() and long_csv.exists()


def save_outputs(
    df_wide: pd.DataFrame,
    df_long: pd.DataFrame,
    source_file: Path,
    clean_dir: Path,
    overwrite: bool = False,
) -> tuple[Path, Path] | None:
    clean_dir.mkdir(parents=True, exist_ok=True)
    wide_csv, long_csv = output_paths_for_excel(source_file, clean_dir)

    if not overwrite and wide_csv.exists() and long_csv.exists():
        return None

    if overwrite or not wide_csv.exists():
        df_wide.to_csv(wide_csv, index=False)

    if overwrite or not long_csv.exists():
        df_long.to_csv(long_csv, index=False)

    return wide_csv, long_csv


def process_excel_file(
    file_path: Path,
    clean_dir: Path,
    sheet_name: str = DEFAULT_SHEET_NAME,
    overwrite: bool = False,
) -> dict:
    if not overwrite and outputs_exist_for_excel(file_path, clean_dir):
        wide_csv, long_csv = output_paths_for_excel(file_path, clean_dir)
        return {
            "source_file": file_path,
            "status": "skipped",
            "wide_csv": wide_csv,
            "long_csv": long_csv,
            "rows_wide": None,
            "rows_long": None,
            "columns": None,
        }

    df_wide, df_long = load_and_clean_production_data(
        file_path=file_path,
        sheet_name=sheet_name,
    )
    saved = save_outputs(
        df_wide=df_wide,
        df_long=df_long,
        source_file=file_path,
        clean_dir=clean_dir,
        overwrite=overwrite,
    )

    if saved is None:
        wide_csv, long_csv = output_paths_for_excel(file_path, clean_dir)
        status = "skipped"
    else:
        wide_csv, long_csv = saved
        status = "written"

    return {
        "source_file": file_path,
        "status": status,
        "wide_csv": wide_csv,
        "long_csv": long_csv,
        "rows_wide": len(df_wide),
        "rows_long": len(df_long),
        "columns": df_wide.columns.tolist(),
    }


def process_excel_files(
    clean_dir: Path,
    raw_dir: Path | None = None,
    files: Iterable[Path | str] | None = None,
    sheet_name: str = DEFAULT_SHEET_NAME,
    overwrite: bool = False,
) -> list[dict]:
    excel_files = iter_excel_files(raw_dir=raw_dir, files=files)

    results: list[dict] = []
    for file_path in excel_files:
        results.append(
            process_excel_file(
                file_path=file_path,
                clean_dir=clean_dir,
                sheet_name=sheet_name,
                overwrite=overwrite,
            )
        )

    return results
