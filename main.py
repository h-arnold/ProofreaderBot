"""Command-line entrypoint for the WJEC document scraper."""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Iterable
from urllib.parse import urlparse

from wjec_scraper import QUALIFICATION_URLS, download_subject_pdfs, iter_subject_pdf_links


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Download PDF documents for the WJEC GCSE Made-for-Wales qualifications.",
    )
    parser.add_argument(
        "--subjects",
        nargs="*",
        metavar="SUBJECT",
        help="Optional list of subject names to download (defaults to all configured subjects).",
    )
    parser.add_argument(
        "-o",
        "--output",
        default="Documents",
        help="Root directory where subject folders will be saved.",
    )
    parser.add_argument(
        "--list-subjects",
        action="store_true",
        help="List all available subjects and exit.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show which files would be downloaded without saving them.",
    )
    return parser


def normalise_subject_names(subjects: Iterable[str]) -> set[str]:
    return {subject.strip().lower() for subject in subjects}


def resolve_subjects(subject_args: list[str] | None) -> tuple[dict[str, str], set[str]]:
    if not subject_args:
        return dict(QUALIFICATION_URLS), set()

    requested = normalise_subject_names(subject_args)
    selected = {
        subject: url for subject, url in QUALIFICATION_URLS.items() if subject.lower() in requested
    }
    missing = requested.difference({subject.lower() for subject in selected})
    return selected, missing


def run_cli(args: argparse.Namespace) -> int:
    if args.list_subjects:
        print("Available subjects:")
        for subject in sorted(QUALIFICATION_URLS):
            print(f" - {subject}")
        return 0

    selected_subjects, missing = resolve_subjects(args.subjects)
    if missing:
        print("Warning: some requested subjects were not recognised:")
        for item in sorted(missing):
            print(f"  - {item}")

    if not selected_subjects:
        print("No subjects selected. Exiting.")
        return 1

    output_root = Path(args.output)
    if not args.dry_run:
        output_root.mkdir(parents=True, exist_ok=True)

    total_downloaded = 0
    for subject, url in selected_subjects.items():
        print(f"\n=== {subject} ===")
        if args.dry_run:
            pdf_links = list(iter_subject_pdf_links(url))
            if not pdf_links:
                print("No PDF links found.")
                continue
            for pdf_url, title in pdf_links:
                label = title or Path(urlparse(pdf_url).path).name
                print(f"Would download: {label} ({pdf_url})")
            total_downloaded += len(pdf_links)
            continue

        count, subject_dir = download_subject_pdfs(
            subject,
            url,
            output_root,
            reporter=lambda label, destination, pdf_url: print(
                f"Downloading {label} -> {destination}"
            ),
        )
        if count == 0:
            print("No PDF links found.")
        else:
            print(f"Saved {count} PDF(s) to {subject_dir}")
            total_downloaded += count

    if args.dry_run:
        print(f"\nDry run complete. {total_downloaded} PDF(s) would be downloaded.")
    else:
        print(f"\nFinished. Downloaded {total_downloaded} PDF(s) into {output_root.resolve()}")

    return 0


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    return run_cli(args)


if __name__ == "__main__":
    raise SystemExit(main())
