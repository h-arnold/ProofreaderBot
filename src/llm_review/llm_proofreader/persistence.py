"""Persistence utilities for the LLM proofreader.

Handles saving proofreader results to per-document CSV files.
"""

from __future__ import annotations

import csv
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from src.models import LanguageIssue


def save_proofreader_results(
    output_path: Path,
    results: list[LanguageIssue],
    *,
    columns: list[str] | None = None,
) -> None:
    """Save proofreader results to a CSV file.

    Args:
        output_path: Path to output CSV file
        results: List of LanguageIssue objects to save
        columns: List of column names to include (default: standard columns)
    """
    if columns is None:
        columns = [
            "issue_id",
            "page_number",
            "issue",
            "highlighted_context",
            "pass_code",
            "error_category",
            "confidence_score",
            "reasoning",
        ]

    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=columns)
        writer.writeheader()

        for result in results:
            row = {}
            for col in columns:
                value = getattr(result, col, None)
                if value is None:
                    row[col] = ""
                elif hasattr(value, "value"):
                    # Handle enums
                    row[col] = value.value
                else:
                    row[col] = str(value)
            writer.writerow(row)

    print(f"  Saved {len(results)} result(s) to {output_path}")
