"""Load categorised issues from the LLM categoriser output.

This module parses the aggregated llm_categorised-language-check-report.csv
which has a different structure from the raw language-check-report.csv.

CSV columns:
    - Subject
    - Filename
    - issue_id
    - page_number
    - issue
    - highlighted_context
    - pass_code
    - error_category
    - confidence_score
    - reasoning
"""

from __future__ import annotations

import csv
from pathlib import Path
from typing import Generator

from src.models import DocumentKey, ErrorCategory, LanguageIssue, PassCode


def load_categorised_issues(
    report_path: Path,
    *,
    subjects: set[str] | None = None,
    documents: set[str] | None = None,
) -> dict[DocumentKey, list[LanguageIssue]]:
    """Load and group categorised issues from the LLM categoriser output.

    Args:
        report_path: Path to llm_categorised-language-check-report.csv
        subjects: Optional set of subject filters (case-insensitive)
        documents: Optional set of document filters (case-insensitive)

    Returns:
        Dictionary mapping DocumentKey to list of LanguageIssue objects
    """
    raw_issues = list(_parse_categorised_csv(report_path))

    # Apply filters
    if subjects:
        raw_issues = [
            (subj, fname, issue)
            for subj, fname, issue in raw_issues
            if any(s.lower() in subj.lower() for s in subjects)
        ]

    if documents:
        raw_issues = [
            (subj, fname, issue)
            for subj, fname, issue in raw_issues
            if any(d.lower() in fname.lower() for d in documents)
        ]

    # Group by DocumentKey
    grouped: dict[DocumentKey, list[LanguageIssue]] = {}
    for subject, filename, issue in raw_issues:
        key = DocumentKey(subject=subject, filename=filename)
        if key not in grouped:
            grouped[key] = []
        grouped[key].append(issue)

    return grouped


def _parse_categorised_csv(
    report_path: Path,
) -> Generator[tuple[str, str, LanguageIssue], None, None]:
    """Parse the categorised CSV file.

    Yields:
        Tuples of (subject, filename, LanguageIssue)
    """
    if not report_path.exists():
        raise FileNotFoundError(f"Report not found: {report_path}")

    required_columns = {
        "Subject",
        "Filename",
        "issue_id",
        "page_number",
        "issue",
        "highlighted_context",
        "pass_code",
        "error_category",
        "confidence_score",
        "reasoning",
    }

    with open(report_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)

        # Validate headers
        if not reader.fieldnames:
            raise ValueError("CSV file has no headers")

        header_set = set(reader.fieldnames)
        missing = required_columns - header_set
        if missing:
            raise ValueError(f"CSV missing required columns: {missing}")

        for row in reader:
            try:
                subject = row["Subject"].strip()
                filename = row["Filename"].strip()

                # Parse error_category - handle "ErrorCategory.VALUE" format
                error_category_raw = row.get("error_category", "").strip()
                error_category: ErrorCategory | None = None
                if error_category_raw:
                    if error_category_raw.startswith("ErrorCategory."):
                        error_category_value = error_category_raw.split(".", 1)[1]
                    else:
                        error_category_value = error_category_raw
                    # Convert to enum
                    try:
                        error_category = ErrorCategory(error_category_value)
                    except ValueError:
                        print(f"Warning: Invalid error category '{error_category_raw}'")
                        error_category = None

                # Parse the issue - note that the categorised CSV doesn't have
                # all the original detection fields, so we'll create a minimal
                # LanguageIssue with what we have. Use placeholder values for
                # required fields that aren't in the categorised CSV.
                issue = LanguageIssue(
                    filename=filename,
                    rule_id="VERIFIER_REVIEW",  # Placeholder - not in categorised CSV
                    message="Review by categoriser verifier",  # Placeholder
                    issue_type="review",  # Placeholder
                    replacements=[],  # Not in categorised CSV
                    context=row[
                        "highlighted_context"
                    ].strip(),  # Use highlighted_context
                    highlighted_context=row["highlighted_context"].strip(),
                    issue=row["issue"].strip(),
                    page_number=int(row["page_number"]),
                    issue_id=int(row["issue_id"]),
                    pass_code=PassCode.LTC,
                    error_category=error_category,
                    confidence_score=(
                        int(row["confidence_score"])
                        if row.get("confidence_score")
                        else None
                    ),
                    reasoning=row.get("reasoning", "").strip() or None,
                )

                yield subject, filename, issue

            except (ValueError, KeyError) as e:
                print(f"Warning: Skipping invalid row: {e}")
                continue
