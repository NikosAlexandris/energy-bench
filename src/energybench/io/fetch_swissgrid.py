from __future__ import annotations

from pathlib import Path
import re
from typing import Iterable

import requests
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait


TARGET_PAGE = (
    "https://www.swissgrid.ch/en/home/operation/grid-data/"
    "generation.html#end-user-consumption"
)

DEFAULT_CHROMIUM_BINARY = "/usr/sbin/chromium"
DEFAULT_CHROMEDRIVER = "/usr/bin/chromedriver"


def make_driver(
    chromium_binary: str = DEFAULT_CHROMIUM_BINARY,
    chromedriver_path: str = DEFAULT_CHROMEDRIVER,
    headless: bool = True,
) -> webdriver.Chrome:
    options = Options()
    options.binary_location = chromium_binary
    if headless:
        options.add_argument("--headless=new")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")

    service = Service(chromedriver_path)
    return webdriver.Chrome(service=service, options=options)


def extract_excel_links(
    page_url: str = TARGET_PAGE,
    chromium_binary: str = DEFAULT_CHROMIUM_BINARY,
    chromedriver_path: str = DEFAULT_CHROMEDRIVER,
    headless: bool = True,
    timeout: int = 20,
) -> list[str]:
    driver = make_driver(
        chromium_binary=chromium_binary,
        chromedriver_path=chromedriver_path,
        headless=headless,
    )

    try:
        driver.get(page_url)
        WebDriverWait(driver, timeout).until(
            lambda d: len(d.find_elements(By.TAG_NAME, "a")) > 0
        )

        links: list[str] = []
        seen: set[str] = set()

        for link in driver.find_elements(By.TAG_NAME, "a"):
            href = link.get_attribute("href")
            if not href:
                continue
            if not href.lower().endswith(".xlsx"):
                continue
            if href in seen:
                continue
            seen.add(href)
            links.append(href)

        return sorted(links)
    finally:
        driver.quit()


def extract_year_from_url(url: str) -> int | None:
    match = re.search(r"(20\d{2})", url)
    if not match:
        return None
    return int(match.group(1))


def filter_links_by_years(
    urls: Iterable[str],
    years: Iterable[int] | None = None,
) -> list[str]:
    urls = list(urls)

    if years is None:
        return urls

    year_set = set(years)
    kept: list[str] = []

    for url in urls:
        year = extract_year_from_url(url)
        if year is not None and year in year_set:
            kept.append(url)

    return kept


def download_file(
    url: str,
    download_dir: Path,
    overwrite: bool = False,
    timeout: int = 60,
) -> Path:
    download_dir.mkdir(parents=True, exist_ok=True)

    filename = url.split("/")[-1]
    output_path = download_dir / filename

    if output_path.exists() and not overwrite:
        return output_path

    response = requests.get(url, timeout=timeout)
    response.raise_for_status()
    output_path.write_bytes(response.content)

    return output_path


def download_excel_files(
    urls: Iterable[str],
    download_dir: Path,
    overwrite: bool = False,
    timeout: int = 60,
) -> tuple[list[Path], list[Path]]:
    downloaded: list[Path] = []
    skipped: list[Path] = []

    for url in urls:
        filename = url.split("/")[-1]
        output_path = download_dir / filename

        if output_path.exists() and not overwrite:
            skipped.append(output_path)
            continue

        path = download_file(
            url=url,
            download_dir=download_dir,
            overwrite=overwrite,
            timeout=timeout,
        )
        downloaded.append(path)

    return downloaded, skipped


def fetch_swissgrid_excels(
    download_dir: Path,
    years: Iterable[int] | None = None,
    overwrite: bool = False,
    page_url: str = TARGET_PAGE,
    chromium_binary: str = DEFAULT_CHROMIUM_BINARY,
    chromedriver_path: str = DEFAULT_CHROMEDRIVER,
    headless: bool = True,
    timeout: int = 20,
) -> dict[str, list]:
    urls = extract_excel_links(
        page_url=page_url,
        chromium_binary=chromium_binary,
        chromedriver_path=chromedriver_path,
        headless=headless,
        timeout=timeout,
    )

    selected_urls = filter_links_by_years(urls, years=years)
    downloaded, skipped = download_excel_files(
        urls=selected_urls,
        download_dir=download_dir,
        overwrite=overwrite,
    )

    return {
        "urls_found": urls,
        "urls_selected": selected_urls,
        "downloaded": downloaded,
        "skipped": skipped,
    }
