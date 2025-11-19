"""Persist verified results as a single aggregated CSV file.

This module handles atomic writes of the aggregated CSV output file.
Unlike llm_categoriser which writes per-document CSVs, the verifier
writes all results to a single file:
    Documents/verified-llm-categorised-language-check-report.csv

The CSV includes subject and filename columns to identify the source document.
"""

from __future__ import annotations

import csv
from pathlib import Path
from typing import Any

from src.models.document_key import DocumentKey

from .config import VerifierConfiguration

# CSV headers for verifier output (includes subject and filename)
CSV_HEADERS = [
    "subject",
    "filename",
    "issue_id",
    "page_number",
    "issue",
    "highlighted_context",
    "pass_code",
    "error_category",
    "confidence_score",
    "reasoning",
]


class VerifierPersistenceManager:
    """Persistence manager for aggregated verifier output."""

    def __init__(self, config: VerifierConfiguration):
        self.config = config
        self.aggregated_results: list[dict[str, Any]] = []

    def add_batch_results(
        self,
        key: DocumentKey,
        batch_results: list[dict[str, Any]],
    ) -> None:
        """Add batch results to the in-memory aggregated results.

        Args:
            key: DocumentKey identifying the document
            batch_results: List of issue dictionaries
        """
        # Add subject and filename to each result
        for result in batch_results:
            result["subject"] = key.subject
            result["filename"] = key.filename
            self.aggregated_results.append(result)

    def write_aggregated_results(self, output_path: Path) -> Path:
        """Write all accumulated results to a single CSV file.

        Args:
            output_path: Path to the output CSV file

        Returns:
            Path to the saved file
        """
        if not self.aggregated_results:
            print("No results to write")
            return output_path

        # Ensure parent directory exists
        output_path.parent.mkdir(parents=True, exist_ok=True)

        # Write atomically
        temp_file = output_path.with_suffix(".tmp")
        try:
            with open(temp_file, "w", encoding="utf-8", newline="") as f:
                writer = csv.DictWriter(f, fieldnames=CSV_HEADERS)
                writer.writeheader()

                # Sort by subject, filename, issue_id for consistent output
                sorted_results = sorted(
                    self.aggregated_results,
                    key=lambda r: (
                        r.get("subject", ""),
                        r.get("filename", ""),
                        r.get("issue_id", 0),
                    ),
                )

                for result in sorted_results:
                    # Extract only the columns we need
                    row = {col: result.get(col, "") for col in CSV_HEADERS}
                    writer.writerow(row)

            temp_file.replace(output_path)
            print(
                f"\nWrote {len(self.aggregated_results)} verified issues to {output_path}"
            )

        except OSError as e:
            print(f"Error writing to {output_path}: {e}")
            if temp_file.exists():
                temp_file.unlink()
            raise

        return output_path

    def clear(self) -> None:
        """Clear accumulated results."""
        self.aggregated_results.clear()
