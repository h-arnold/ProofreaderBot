"""Command line tool for downloading PDF documents from the WJEC GCSE Art and Design page."""

from __future__ import annotations

import argparse
import itertools
import re
from pathlib import Path
from typing import Iterable
from urllib.parse import urljoin, urlparse

import requests
from bs4 import BeautifulSoup


DEFAULT_URL = "https://www.wjec.co.uk/qualifications/gcse-art-and-design-teaching-from-2025/#tab_keydocuments"


def fetch_html(url: str) -> str:
    response = requests.get(url, timeout=30)
    response.raise_for_status()
    return response.text


def iter_pdf_links(soup: BeautifulSoup, base_url: str) -> Iterable[tuple[str, str]]:
    seen: set[str] = set()
    for anchor in soup.find_all("a", href=True):
        href = anchor["href"].strip()
        if not href.lower().endswith(".pdf"):
            continue
        absolute_url = urljoin(base_url, href)
        if absolute_url in seen:
            continue
        seen.add(absolute_url)
        title = anchor.get_text(strip=True) or Path(urlparse(absolute_url).path).name
        yield title, absolute_url


def sanitise_filename(title: str, url: str, existing: set[str]) -> str:
    stem = re.sub(r"[^a-zA-Z0-9._-]+", "-", title.lower()).strip("-")
    if not stem:
        stem = Path(urlparse(url).path).stem or "document"
    if not stem.endswith(".pdf"):
        stem = f"{stem}.pdf"
    base_stem = stem
    for idx in itertools.count(1):
        if stem not in existing:
            existing.add(stem)
            return stem
        stem = f"{Path(base_stem).stem}-{idx}.pdf"


def download_file(url: str, destination: Path) -> None:
    with requests.get(url, stream=True, timeout=60) as response:
        response.raise_for_status()
        with destination.open("wb") as file_handle:
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    file_handle.write(chunk)


def main() -> None:
    parser = argparse.ArgumentParser(description="Download PDF documents listed on the WJEC GCSE Art and Design page.")
    parser.add_argument("url", nargs="?", default=DEFAULT_URL, help="Target page URL to scrape")
    parser.add_argument("-o", "--output", default="downloads", help="Directory where PDFs will be saved")
    args = parser.parse_args()

    output_directory = Path(args.output)
    output_directory.mkdir(parents=True, exist_ok=True)

    print(f"Fetching page: {args.url}")
    html = fetch_html(args.url)
    soup = BeautifulSoup(html, "html.parser")

    pdf_links = list(iter_pdf_links(soup, args.url))
    if not pdf_links:
        print("No PDF links found.")
        return

    used_filenames: set[str] = set()
    for title, pdf_url in pdf_links:
        filename = sanitise_filename(title or pdf_url, pdf_url, used_filenames)
        destination = output_directory / filename
        print(f"Downloading {title or filename} -> {destination}")
        download_file(pdf_url, destination)

    print(f"Downloaded {len(pdf_links)} PDF(s) to {output_directory.resolve()}")


if __name__ == "__main__":
    main()
