"""Tests for the categoriser verifier module.

These tests verify the basic functionality of the verifier including:
- Configuration setup
- Prompt building
- Response validation
- Persistence
"""

from __future__ import annotations

import sys
from pathlib import Path
from unittest.mock import MagicMock

# Add project root to path
PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

# ruff: noqa: E402
from src.llm_review.categoriser_verifier.config import VerifierConfiguration
from src.llm_review.categoriser_verifier.persistence import (
    CSV_HEADERS,
    VerifierPersistenceManager,
)
from src.llm_review.categoriser_verifier.prompt_factory import build_prompts
from src.llm_review.categoriser_verifier.runner import VerifierRunner
from src.llm_review.core.batcher import Batch
from src.models import DocumentKey, LanguageIssue, PassCode


class TestVerifierConfiguration:
    """Test the VerifierConfiguration dataclass."""

    def test_default_configuration(self):
        """Test creating a default configuration."""
        config = VerifierConfiguration(
            input_csv_path=Path("Documents/llm_categorised-language-check-report.csv"),
            output_base_dir=Path("Documents"),
            output_subdir="verifier_reports",
            aggregated_output_path=Path(
                "Documents/verified-llm-categorised-language-check-report.csv"
            ),
            batch_size=10,
            max_retries=2,
            state_file=Path("data/verifier_state.json"),
            subjects=None,
            documents=None,
            llm_provider=None,
            fail_on_quota=True,
            log_raw_responses=False,
            log_response_dir=Path("data/verifier_responses"),
            output_csv_columns=CSV_HEADERS,
        )

        assert config.batch_size == 10
        assert config.max_retries == 2
        assert config.aggregated_output_path == Path(
            "Documents/verified-llm-categorised-language-check-report.csv"
        )


class TestVerifierPersistence:
    """Test the VerifierPersistenceManager."""

    def test_add_batch_results(self):
        """Test adding batch results to the manager."""
        config = VerifierConfiguration(
            input_csv_path=Path("Documents/llm_categorised-language-check-report.csv"),
            output_base_dir=Path("Documents"),
            output_subdir="verifier_reports",
            aggregated_output_path=Path("Documents/verified.csv"),
            batch_size=10,
            max_retries=2,
            state_file=Path("data/verifier_state.json"),
            subjects=None,
            documents=None,
            llm_provider=None,
            fail_on_quota=True,
            log_raw_responses=False,
            log_response_dir=Path("data"),
            output_csv_columns=CSV_HEADERS,
        )
        manager = VerifierPersistenceManager(config)

        key = DocumentKey(subject="Geography", filename="test.csv")
        results = [
            {
                "issue_id": 0,
                "page_number": 1,
                "issue": "test",
                "highlighted_context": "**test**",
                "pass_code": "PassCode.LTC",
                "error_category": "SPELLING_ERROR",
                "confidence_score": 95,
                "reasoning": "Test reasoning",
            }
        ]

        manager.add_batch_results(key, results)

        assert len(manager.aggregated_results) == 1
        assert manager.aggregated_results[0]["subject"] == "Geography"
        assert manager.aggregated_results[0]["filename"] == "test.csv"

    def test_clear(self):
        """Test clearing accumulated results."""
        config = VerifierConfiguration(
            input_csv_path=Path("Documents/llm_categorised-language-check-report.csv"),
            output_base_dir=Path("Documents"),
            output_subdir="verifier_reports",
            aggregated_output_path=Path("Documents/verified.csv"),
            batch_size=10,
            max_retries=2,
            state_file=Path("data/verifier_state.json"),
            subjects=None,
            documents=None,
            llm_provider=None,
            fail_on_quota=True,
            log_raw_responses=False,
            log_response_dir=Path("data"),
            output_csv_columns=CSV_HEADERS,
        )
        manager = VerifierPersistenceManager(config)

        key = DocumentKey(subject="Geography", filename="test.csv")
        results = [{"issue_id": 0}]
        manager.add_batch_results(key, results)

        assert len(manager.aggregated_results) == 1

        manager.clear()
        assert len(manager.aggregated_results) == 0


class TestPromptFactory:
    """Test prompt building."""

    def test_build_prompts(self):
        """Test that build_prompts returns two prompts."""
        batch = Batch(
            issues=[
                LanguageIssue(
                    filename="test.csv",
                    rule_id="TEST_RULE",
                    message="Test message",
                    issue_type="grammar",
                    replacements=["test"],
                    context="This is a test",
                    highlighted_context="This is a **test**",
                    issue="test",
                    page_number=1,
                    issue_id=0,
                    pass_code=PassCode.LTC,
                )
            ],
            page_context={1: "# Page 1\n\nThis is a test page."},
            markdown_table="| issue_id | issue |\n|----------|-------|\n| 0 | test |",
            index=0,
            subject="Test Subject",
            filename="test.csv",
        )

        prompts = build_prompts(batch)

        # Should return [system_prompt, user_prompt]
        assert len(prompts) == 2
        assert isinstance(prompts[0], str)
        assert isinstance(prompts[1], str)
        # System prompt should reference the verifier
        assert "verifier" in prompts[0].lower() or "adjudicator" in prompts[0].lower()


class TestVerifierRunner:
    """Test the VerifierRunner."""

    def test_runner_initialization(self):
        """Test that the runner initializes correctly."""
        mock_llm_service = MagicMock()
        mock_state = MagicMock()

        runner = VerifierRunner(
            mock_llm_service,
            mock_state,
            batch_size=5,
            max_retries=3,
        )

        assert runner.config.batch_size == 5
        assert runner.config.max_retries == 3
        assert isinstance(runner.persistence, VerifierPersistenceManager)

    def test_validate_response_success(self):
        """Test successful response validation."""
        mock_llm_service = MagicMock()
        mock_state = MagicMock()

        runner = VerifierRunner(mock_llm_service, mock_state)

        issues = [
            LanguageIssue(
                filename="test.csv",
                rule_id="TEST_RULE",
                message="Test message",
                issue_type="grammar",
                replacements=["test"],
                context="This is a test",
                highlighted_context="This is a **test**",
                issue="test",
                page_number=1,
                issue_id=0,
                pass_code=PassCode.LTC,
            )
        ]

        response = [
            {
                "issue_id": 0,
                "error_category": "SPELLING_ERROR",
                "confidence_score": 95,
                "reasoning": "Test reasoning",
            }
        ]

        validated, failed, errors = runner.validate_response(response, issues)

        assert len(validated) == 1
        assert len(failed) == 0
        assert validated[0]["issue_id"] == 0
        assert validated[0]["error_category"] == "SPELLING_ERROR"

    def test_validate_response_invalid_type(self):
        """Test validation with invalid response type."""
        mock_llm_service = MagicMock()
        mock_state = MagicMock()

        runner = VerifierRunner(mock_llm_service, mock_state)

        issues = [
            LanguageIssue(
                filename="test.csv",
                rule_id="TEST_RULE",
                message="Test message",
                issue_type="grammar",
                replacements=["test"],
                context="This is a test",
                highlighted_context="This is a **test**",
                issue="test",
                page_number=1,
                issue_id=0,
                pass_code=PassCode.LTC,
            )
        ]

        # Response is not a list
        response = {"issue_id": 0}

        validated, failed, errors = runner.validate_response(response, issues)

        assert len(validated) == 0
        assert len(failed) == 1
        assert "batch_errors" in errors
