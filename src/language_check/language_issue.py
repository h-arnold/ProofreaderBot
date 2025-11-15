"""Dataclass representing a single detected language issue.

This module now re-exports the unified LanguageIssue model from src.models
for backward compatibility.
"""

from __future__ import annotations

from src.models.language_issue import LanguageIssue

__all__ = ["LanguageIssue"]
