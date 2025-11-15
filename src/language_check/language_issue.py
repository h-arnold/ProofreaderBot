"""Dataclass representing a single detected language issue.

This small module exists to keep the core data model separate from the
scanning and reporting logic. Importing this module is safe from other
language_check modules and helps avoid cyclic import awkwardness when
type-checking.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class LanguageIssue:
    """Represents a single language issue detected in a document."""

    filename: str
    rule_id: str
    message: str
    issue_type: str
    replacements: list[str]
    context: str
    highlighted_context: str
    issue: str
    page_number: int | None = None
    issue_id: int = -1  # Auto-incremented per document by categoriser; -1 = not set
