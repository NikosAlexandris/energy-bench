from __future__ import annotations

from pathlib import Path
import pandas as pd


def plausibility_check(
    csv_file: Path,
    datetime_column: str = "DateTime",
    columns: list[str] | None = None,
    ramp_threshold: float | None = None,
) -> pd.DataFrame:
    df = pd.read_csv(csv_file, parse_dates=[datetime_column]).set_index(datetime_column)

    if columns is None:
        columns = [c for c in df.columns if pd.api.types.is_numeric_dtype(df[c])]

    num = df[columns].apply(pd.to_numeric, errors="coerce")

    rows = []
    for col in columns:
        s = num[col]
        diff = s.diff().abs()

        rows.append({
            "variable": col,
            "negative_count": int((s < 0).sum()),
            "missing_count": int(s.isna().sum()),
            "zero_count": int((s == 0).sum()),
            "max_ramp": float(diff.max()) if not diff.dropna().empty else None,
            "mean_ramp": float(diff.mean()) if not diff.dropna().empty else None,
            "ramp_exceeds_threshold": (
                int((diff > ramp_threshold).sum()) if ramp_threshold is not None else None
            ),
        })

    return pd.DataFrame(rows)
