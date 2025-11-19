from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from src.models.document_key import DocumentKey

from ..core.config import ReviewConfiguration


@dataclass
class VerifierConfiguration(ReviewConfiguration):
    """Configuration for the categoriser verifier review pass."""

    # Override to specify the aggregated output path
    aggregated_output_path: Path | None = None

    def get_output_path(self, key: DocumentKey) -> Path:
        """Get output path for a specific document.

        For verifier, we write to a single aggregated CSV rather than
        per-document files. This method exists for compatibility but
        should not be used directly. Use aggregated_output_path instead.
        """
        if self.aggregated_output_path:
            return self.aggregated_output_path

        # Fallback: per-document structure (not used in normal operation)
        report_dir = self.output_base_dir / key.subject / self.output_subdir
        report_dir.mkdir(parents=True, exist_ok=True)

        # Ensure filename ends with .csv
        filename = key.filename
        if filename.endswith(".md"):
            filename = filename[:-3] + ".csv"
        elif not filename.endswith(".csv"):
            filename += ".csv"

        return report_dir / filename
