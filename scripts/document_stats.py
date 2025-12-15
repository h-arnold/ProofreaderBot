#!/usr/bin/env python3
"""
Script to generate statistics about documents in the Documents folder.

Counts:
- Number of PDF documents per subject
- Number of converted markdown documents per subject
- Total pages per subject (from page markers in markdown)

Usage:
    python -m scripts.document_stats [--documents-dir PATH] [--csv-output CSV] [--per-file] [--file-csv-output CSV]
"""

from __future__ import annotations

import argparse
import csv
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from src.utils.page_utils import find_page_markers


def count_pdfs(subject_dir: Path) -> int:
    """Count PDF documents in the subject's pdfs directory.

    Args:
        subject_dir: Path to the subject directory

    Returns:
        Number of PDF files found
    """
    pdf_dir = subject_dir / "pdfs"
    if not pdf_dir.exists():
        return 0

    return len(list(pdf_dir.glob("*.pdf")))


def count_markdown_files(subject_dir: Path) -> int:
    """Count markdown documents in the subject's markdown directory.

    Args:
        subject_dir: Path to the subject directory

    Returns:
        Number of markdown files found
    """
    markdown_dir = subject_dir / "markdown"
    if not markdown_dir.exists():
        return 0

    return len(list(markdown_dir.glob("*.md")))


def count_total_pages(subject_dir: Path) -> int:
    """Count total pages across all markdown documents in the subject.

    For each markdown document, finds the last page marker {N}----
    If there's no page marker (page 0 only), counts as 1 page.

    Args:
        subject_dir: Path to the subject directory

    Returns:
        Total number of pages across all markdown documents
    """
    markdown_dir = subject_dir / "markdown"
    if not markdown_dir.exists():
        return 0

    total_pages = 0

    for md_file in markdown_dir.glob("*.md"):
        try:
            content = md_file.read_text(encoding="utf-8")
            markers = find_page_markers(content)

            if not markers:
                # No page markers means it's a single page document
                total_pages += 1
            else:
                # Get the last page number and add 1 (pages are 0-indexed)
                last_page = max(marker.page_number for marker in markers)
                total_pages += last_page + 1

        except (IOError, OSError, UnicodeDecodeError) as e:
            print(f"Warning: Could not read {md_file.name}: {e}", file=sys.stderr)
            continue

    return total_pages


def get_markdown_files(subject_dir: Path) -> list[Path]:
    """Return normalised list of markdown files in a subject's markdown directory.

    Args:
        subject_dir: Path to subject directory

    Returns:
        Sorted list of markdown Path objects
    """
    markdown_dir = subject_dir / "markdown"
    if not markdown_dir.exists():
        return []

    return sorted(markdown_dir.glob("*.md"), key=lambda p: p.name.lower())


def count_pages_in_markdown_file(md_file: Path) -> int:
    """Return page count for a markdown file (1 when no markers found).

    Args:
        md_file: Path to a markdown file

    Returns:
        Integer page count
    """
    try:
        content = md_file.read_text(encoding="utf-8")
    except (IOError, OSError, UnicodeDecodeError) as e:
        print(f"Warning: Could not read {md_file}: {e}", file=sys.stderr)
        return 0

    markers = find_page_markers(content)
    if not markers:
        return 1
    last_page = max(marker.page_number for marker in markers)
    return last_page + 1


def get_subject_directories(documents_root: Path) -> list[Path]:
    """Get all subject directories from the Documents folder.

    Args:
        documents_root: Path to the Documents folder

    Returns:
        List of subject directory paths
    """
    if not documents_root.exists():
        return []

    # Get all directories that contain either pdfs or markdown subdirectories
    subjects = []
    for item in documents_root.iterdir():
        if item.is_dir() and ((item / "pdfs").exists() or (item / "markdown").exists()):
            subjects.append(item)

    return sorted(subjects, key=lambda p: p.name)


def main():
    """Main entry point for the script.

    CLI Options:
        --documents-dir: Path to Documents folder (default: ./Documents)
        --csv-output: Optional path to write a CSV summary
        --subjects: Optional list of subject names to include
    """
    parser = argparse.ArgumentParser(
        description="Generate statistics about Documents folder"
    )
    parser.add_argument(
        "--documents-dir",
        type=Path,
        default=Path("Documents"),
        help="Path to Documents folder (default: ./Documents)",
    )
    parser.add_argument(
        "--csv-output",
        type=Path,
        help="Optional CSV path to write summary into",
    )
    parser.add_argument(
        "--subjects",
        nargs="*",
        help="Optional list of subject directory names to include",
    )
    parser.add_argument(
        "--per-file",
        action="store_true",
        help=(
            "Print a breakdown of page counts for each markdown file. "
            "If --csv-output is set and --file-csv-output isn't provided, "
            "a per-file CSV will be written next to the summary file with '-files.csv' suffix."
        ),
    )
    parser.add_argument(
        "--file-csv-output",
        type=Path,
        help=(
            "Optional CSV path to write per-file breakdown into. "
            "If omitted and --csv-output is set, a per-file CSV will be derived next to the summary file."
        ),
    )

    args = parser.parse_args()

    # If the user requested per-file output and gave a per-subject CSV file but
    # did not explicitly provide a per-file CSV path, derive one next to the
    # per-subject CSV with ``-files.csv`` suffix so --per-file + --csv-output
    # also writes file-level CSVs by default.
    if args.per_file and args.csv_output and not args.file_csv_output:
        args.file_csv_output = args.csv_output.with_name(
            f"{args.csv_output.stem}-files.csv"
        )

    documents_root = args.documents_dir

    if not documents_root.exists():
        print(f"Error: Documents folder not found at {documents_root}", file=sys.stderr)
        return 1

    if not documents_root.is_dir():
        print(
            f"Error: Documents path is not a directory: {documents_root}",
            file=sys.stderr,
        )
        return 1

    subjects = get_subject_directories(documents_root)
    if args.subjects:
        wanted = {s.strip().lower() for s in args.subjects if s.strip()}
        subjects = [s for s in subjects if s.name.lower() in wanted]

    if not subjects:
        print("No subject directories found in Documents folder", file=sys.stderr)
        return 1

    # Print header
    header = f"{'Subject':<50} {'PDFs':>8} {'Markdown':>10} {'Pages':>8}"
    print(header)
    print("-" * 80)

    # Track totals
    total_pdfs = 0
    total_markdown = 0
    total_pages = 0

    rows = []
    file_rows: list[tuple[str, str, int]] = []

    # Process each subject
    for subject_dir in subjects:
        subject_name = subject_dir.name
        pdf_count = count_pdfs(subject_dir)
        markdown_count = count_markdown_files(subject_dir)
        page_count = count_total_pages(subject_dir)

        print(f"{subject_name:<50} {pdf_count:>8} {markdown_count:>10} {page_count:>8}")

        total_pdfs += pdf_count
        total_markdown += markdown_count
        total_pages += page_count

        rows.append((subject_name, pdf_count, markdown_count, page_count))

        # Per-file breakdown
        if args.per_file or args.file_csv_output:
            md_files = get_markdown_files(subject_dir)
            if args.per_file and md_files:
                print(f"    {'Filename':<60} {'Pages':>8}")
                print(f"    {'-'*60} {'-'*8}")
            for md_file in md_files:
                pages = count_pages_in_markdown_file(md_file)
                if args.per_file:
                    print(f"    {md_file.name:<50} {pages:>8}")
                if args.file_csv_output:
                    file_rows.append((subject_name, md_file.name, pages))

    # Print totals
    print("-" * 80)
    print(f"{'TOTAL':<50} {total_pdfs:>8} {total_markdown:>10} {total_pages:>8}")

    # Optional CSV output (per-subject summary)
    if args.csv_output:
        csv_path = args.csv_output
        csv_path.parent.mkdir(parents=True, exist_ok=True)
        with csv_path.open("w", newline="", encoding="utf-8") as csv_f:
            writer = csv.writer(csv_f)
            writer.writerow(["Subject", "PDFs", "Markdown", "Pages"])
            for r in rows:
                writer.writerow(r)
            writer.writerow(["TOTAL", total_pdfs, total_markdown, total_pages])
        print(f"Wrote CSV summary to: {csv_path}")

    # Optional per-file CSV output
    if args.file_csv_output:
        file_csv_path = args.file_csv_output
        file_csv_path.parent.mkdir(parents=True, exist_ok=True)
        with file_csv_path.open("w", newline="", encoding="utf-8") as fcsv:
            writer = csv.writer(fcsv)
            writer.writerow(["Subject", "Filename", "Pages"])
            for sr in file_rows:
                writer.writerow(sr)
        print(f"Wrote per-file CSV to: {file_csv_path}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
