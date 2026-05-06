from __future__ import annotations

from pathlib import Path

from cyclopts import App

from energybench.io.fetch_swissgrid import fetch_swissgrid_excels
from energybench.io.clean_swissgrid import process_excel_files


app = App(help="Fetch and clean Swissgrid Excel data.")


@app.command(name="fetch-swissgrid")
def fetch(
    download_dir: Path = Path("data/raw"),
    years: list[int] | None = None,
    overwrite: bool = False,
    headless: bool = True,
    chromium_binary: str = "/usr/sbin/chromium",
    chromedriver_path: str = "/usr/bin/chromedriver",
) -> None:
    result = fetch_swissgrid_excels(
        download_dir=download_dir,
        years=years,
        overwrite=overwrite,
        headless=headless,
        chromium_binary=chromium_binary,
        chromedriver_path=chromedriver_path,
    )

    print(f"Excel links found: {len(result['urls_found'])}")
    print(f"Excel links selected: {len(result['urls_selected'])}")
    print(f"Downloaded: {len(result['downloaded'])}")
    print(f"Skipped existing: {len(result['skipped'])}")

    for path in result["downloaded"]:
        print(f" + {path}")

    for path in result["skipped"]:
        print(f" = {path}")


@app.command(name="clean-swissgrid")
def clean(
    clean_dir: Path = Path("data/clean"),
    raw_dir: Path = Path("data/raw"),
    files: list[Path] | None = None,
    sheet_name: str = "Zeitreihen0h15",
    overwrite: bool = False,
) -> None:
    results = process_excel_files(
        clean_dir=clean_dir,
        raw_dir=None if files else raw_dir,
        files=files,
        sheet_name=sheet_name,
        overwrite=overwrite,
    )

    for result in results:
        print(
            f"[{result['status']}] {result['source_file'].name} "
            f"-> {result['wide_csv'].name}, {result['long_csv'].name}"
        )
