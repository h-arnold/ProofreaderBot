"""Merge CSV reports located inside subject sub-folders.

Given a sub-folder name (for example ``document_reports`` or
``llm_page_proofreader_reports``) this module walks every subject directory
within the ``Documents`` tree, collects the CSV files that live inside that
sub-folder, and merges them into a single CSV file. The merged output always
contains two leading columns (``Subject`` and ``Filename``) followed by the
standard per-document headers defined in :mod:`src.llm_review`.

The public ``merge_document_reports`` helper can be imported by other scripts
or tests. Additional filters allow callers to restrict the merge to specific
subjects or CSV filenames, and an explicit output path can be supplied when
writing outside the default ``Documents`` directory.
"""

from __future__ import annotations

import csv
import sys
from pathlib import Path
from typing import Iterable, Iterator, List

# Match the headers expected from per-document CSVs
ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from src.llm_review.llm_categoriser.persistence import CSV_HEADERS

DEFAULT_DOCUMENTS_DIR = Path("Documents")
DEFAULT_OUTPUT_FILE = "llm_categorised-language-check-report.csv"


def _normalise_subject_filter(subjects: Iterable[str] | None) -> set[str] | None:
    """Return a lowercase subject filter set or ``None`` when no filter."""

    if not subjects:
        return None

    normalised = {subject.strip().lower() for subject in subjects if subject.strip()}
    return normalised or None


def _normalise_filename_filter(filenames: Iterable[str] | None) -> set[str] | None:
    """Return a lowercase filename filter set or ``None`` when no filter."""

    if not filenames:
        return None

    normalised: set[str] = set()
    for name in filenames:
        cleaned = Path(name).name
        if not cleaned:
            continue
        if not cleaned.lower().endswith(".csv"):
            cleaned = f"{cleaned}.csv"
        normalised.add(cleaned.lower())
    return normalised or None


def _iter_subject_directories(documents_dir: Path) -> Iterator[Path]:
    """Yield sorted subject directories inside ``documents_dir``."""

    if not documents_dir.exists():
        return

    subject_dirs = [p for p in documents_dir.iterdir() if p.is_dir()]
    subject_dirs.sort(key=lambda p: p.name.lower())
    for subject_dir in subject_dirs:
        yield subject_dir


def _iter_subject_csvs(
    documents_dir: Path,
    subfolder: Path,
    subject_filter: set[str] | None,
    filename_filter: set[str] | None,
) -> Iterator[tuple[str, Path]]:
    """Yield ``(subject_name, csv_path)`` tuples for matching CSV files."""

    if subfolder.is_absolute():
        raise ValueError("subfolder must be a relative path")

    for subject_dir in _iter_subject_directories(documents_dir):
        subject_name = subject_dir.name
        if subject_filter and subject_name.lower() not in subject_filter:
            continue

        target_dir = subject_dir.joinpath(subfolder)
        if not target_dir.is_dir():
            continue

        csv_files = sorted(target_dir.glob("*.csv"), key=lambda p: p.name.lower())
        for csv_path in csv_files:
            if filename_filter and csv_path.name.lower() not in filename_filter:
                continue
            yield subject_name, csv_path


def _resolve_output_path(
    documents_dir: Path,
    output_path: Path | None,
    output_file_name: str,
) -> Path:
    """Return the full path where the merged CSV should be written."""

    if output_path is not None:
        return output_path
    return documents_dir / output_file_name


def merge_document_reports(
    subfolder_name: str,
    *,
    documents_dir: Path = DEFAULT_DOCUMENTS_DIR,
    output_path: Path | None = None,
    output_file_name: str = DEFAULT_OUTPUT_FILE,
    subjects: Iterable[str] | None = None,
    filenames: Iterable[str] | None = None,
) -> Path:
    """Merge CSV files contained in a subject sub-folder.

    Args:
        subfolder_name: Relative path of the sub-folder inside each subject
            directory (for example ``document_reports``).
        documents_dir: Root folder containing subject directories. Defaults to
            ``Documents`` in the project root when not provided.
        output_path: Optional explicit file path for the merged CSV.
        output_file_name: Filename to write inside ``documents_dir`` when
            ``output_path`` is not supplied.
        subjects: Optional iterable of subject directory names to include.
        filenames: Optional iterable of CSV filenames to include. Filenames can
            be supplied with or without the ``.csv`` extension.

    Returns:
        Path to the merged CSV file that was written.
    """

    subfolder = Path(subfolder_name)
    documents_dir = Path(documents_dir)
    output_path = _resolve_output_path(documents_dir, output_path, output_file_name)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    subject_filter = _normalise_subject_filter(subjects)
    filename_filter = _normalise_filename_filter(filenames)

    headers: List[str] = ["Subject", "Filename"] + CSV_HEADERS
    csv_sources = list(
        _iter_subject_csvs(documents_dir, subfolder, subject_filter, filename_filter)
    )

    with output_path.open("w", encoding="utf-8", newline="") as out_f:
        writer = csv.DictWriter(out_f, fieldnames=headers)
        writer.writeheader()

        for subject_name, csv_path in csv_sources:
            with csv_path.open("r", encoding="utf-8", newline="") as in_f:
                reader = csv.DictReader(in_f)
                for row in reader:
                    normalised = {header: row.get(header, "") for header in CSV_HEADERS}
                    merged_row = {"Subject": subject_name, "Filename": csv_path.name}
                    merged_row.update(normalised)
                    writer.writerow(merged_row)

    return output_path


def main() -> None:
    import argparse

    parser = argparse.ArgumentParser(
        description="Merge CSV reports inside subject sub-folders"
    )
    parser.add_argument(
        "subfolder",
        nargs="?",
        default="document_reports",
        help="Relative sub-folder name within each subject directory",
    )
    parser.add_argument(
        "--documents-dir",
        "-d",
        default=str(DEFAULT_DOCUMENTS_DIR),
        help="Path to the Documents root (default: Documents)",
    )
    parser.add_argument(
        "--output-file",
        "-f",
        default=DEFAULT_OUTPUT_FILE,
        help="Name of the merged file to write when --output-path is not supplied",
    )
    parser.add_argument(
        "--output-path",
        "-p",
        help="Explicit path for the merged CSV; overrides --output-file",
    )
    parser.add_argument(
        "--subjects",
        "-s",
        nargs="+",
        help="Optional list of subject directory names to include",
    )
    parser.add_argument(
        "--filenames",
        "-n",
        nargs="+",
        help="Optional list of CSV filenames to include (with or without .csv)",
    )

    args = parser.parse_args()

    merged = merge_document_reports(
        args.subfolder,
        documents_dir=Path(args.documents_dir),
        output_path=Path(args.output_path) if args.output_path else None,
        output_file_name=args.output_file,
        subjects=args.subjects,
        filenames=args.filenames,
    )
    print(f"Wrote merged report to: {merged}")


if __name__ == "__main__":
    main()
