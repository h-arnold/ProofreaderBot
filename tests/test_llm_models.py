from __future__ import annotations

import sys
from pathlib import Path

# Add project root to path
PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from pydantic import ValidationError

from src.models import ErrorCategory, LanguageIssue


def test_llm_language_issue_valid() -> None:
    """Test creating a LanguageIssue from LLM response format."""
    data = {
        "rule_from_tool": "EN_QUOTES",
        "type_from_tool": "grammar",
        "message_from_tool": "Use smart quotes.",
        "suggestions_from_tool": "Use ' and ' instead of '",
        "context_from_tool": "she said 'hello'",
        "error_category": "PARSING_ERROR",
        "confidence_score": 87,
        "reasoning": "Tool flags ASCII quotes where typographic ones are expected.",
    }

    issue = LanguageIssue.from_llm_response(data, filename="test.md")
    assert isinstance(issue, LanguageIssue)
    assert issue.error_category == ErrorCategory.PARSING_ERROR
    assert issue.replacements == ["Use ' and ' instead of '"]
    assert issue.filename == "test.md"
    assert issue.rule_id == "EN_QUOTES"
    assert issue.issue_type == "grammar"


def test_llm_language_issue_invalid_confidence() -> None:
    """Test that invalid confidence scores are rejected."""
    data = {
        "rule_from_tool": "EN_QUOTES",
        "type_from_tool": "grammar",
        "message_from_tool": "Use smart quotes.",
        "suggestions_from_tool": ["Use ' and '"],
        "context_from_tool": "she said 'hello'",
        "error_category": ErrorCategory.PARSING_ERROR,
        "confidence_score": 150,
        "reasoning": "Too high confidence.",
    }
    try:
        LanguageIssue.from_llm_response(data, filename="test.md")
        assert False, "Expected ValidationError for confidence_score"
    except ValidationError as exc:
        assert "confidence_score must be between 0 and 100" in str(exc)


def test_llm_language_issue_missing_required() -> None:
    """Test that empty required fields are rejected."""
    data = {
        "rule_from_tool": "",
        "type_from_tool": "",
        "message_from_tool": "",
        "suggestions_from_tool": [],
        "context_from_tool": "",
        "error_category": "FALSE_POSITIVE",
        "confidence_score": 10,
        "reasoning": "",
    }

    try:
        LanguageIssue.from_llm_response(data, filename="test.md")
        assert False, "Expected ValidationError because several fields are empty"
    except ValidationError as exc:
        assert "must not be empty" in str(exc)


def test_language_issue_direct_creation() -> None:
    """Test creating a LanguageIssue directly (for LanguageTool detection use case)."""
    issue = LanguageIssue(
        filename="test.md",
        rule_id="TEST_RULE",
        message="This is a test",
        issue_type="grammar",
        replacements=["fix1", "fix2"],
        context="plain context",
        highlighted_context="**highlighted** context",
        issue="highlighted",
        page_number=5,
        issue_id=0,
    )
    
    assert issue.filename == "test.md"
    assert issue.rule_id == "TEST_RULE"
    assert issue.error_category is None  # Not LLM-categorised
    assert issue.confidence_score is None
    assert issue.reasoning is None


def test_language_issue_with_llm_fields() -> None:
    """Test creating a LanguageIssue with both tool and LLM fields."""
    issue = LanguageIssue(
        filename="test.md",
        rule_id="TEST_RULE",
        message="This is a test",
        issue_type="grammar",
        replacements=["fix1"],
        context="context",
        highlighted_context="**context**",
        issue="context",
        page_number=5,
        issue_id=0,
        error_category=ErrorCategory.SPELLING_ERROR,
        confidence_score=90,
        reasoning="This is clearly a spelling error",
    )
    
    assert issue.error_category == ErrorCategory.SPELLING_ERROR
    assert issue.confidence_score == 90
    assert issue.reasoning == "This is clearly a spelling error"


def test_language_issue_partial_llm_fields_rejected() -> None:
    """Test that partial LLM categorisation is rejected."""
    try:
        LanguageIssue(
            filename="test.md",
            rule_id="TEST_RULE",
            message="This is a test",
            issue_type="grammar",
            replacements=[],
            context="context",
            highlighted_context="**context**",
            issue="context",
            error_category=ErrorCategory.SPELLING_ERROR,
            # Missing confidence_score and reasoning
        )
        assert False, "Expected ValidationError for partial LLM fields"
    except ValidationError as exc:
        assert "all be provided" in str(exc)
