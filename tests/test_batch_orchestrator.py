"""Tests for batch orchestrator functionality."""

from __future__ import annotations

import os
import sys
from pathlib import Path
from typing import Any, Sequence
from unittest.mock import MagicMock


# Fix imports to work with pytest
try:
    from src.llm_review.llm_categoriser.batch_orchestrator import (
        BatchJobMetadata,
        BatchJobTracker,
        BatchOrchestrator,
    )
    from src.llm_review.llm_categoriser.state import CategoriserState
    from src.llm.provider import LLMProvider
    from src.llm.service import LLMService
except ImportError:
    PROJECT_ROOT = Path(__file__).resolve().parents[1]
    if str(PROJECT_ROOT) not in sys.path:
        sys.path.insert(0, str(PROJECT_ROOT))
    from src.llm_review.llm_categoriser.batch_orchestrator import (
        BatchJobMetadata,
        BatchJobTracker,
        BatchOrchestrator,
    )
    from src.llm_review.llm_categoriser.state import CategoriserState
    from src.llm.provider import LLMProvider
    from src.llm.service import LLMService


class _DummyProvider(LLMProvider):
    """Dummy provider for testing."""
    
    name = "dummy"
    
    def __init__(self) -> None:
        self.created_jobs = []
        self.job_statuses = {}
        self.job_results = {}
    
    def generate(self, user_prompts: Sequence[str], *, filter_json: bool = False) -> Any:
        return []
    
    def batch_generate(self, batch_payload: Sequence[Sequence[str]], *, filter_json: bool = False) -> Sequence[Any]:
        raise NotImplementedError()
    
    def create_batch_job(self, batch_payload: Sequence[Sequence[str]], *, filter_json: bool = False) -> str:
        job_name = f"job-{len(self.created_jobs)}"
        self.created_jobs.append((job_name, batch_payload))
        self.job_statuses[job_name] = MagicMock(done=False, state="PENDING")
        return job_name
    
    def get_batch_job(self, batch_job_name: str) -> Any:
        return self.job_statuses.get(batch_job_name)
    
    def fetch_batch_results(self, batch_job_name: str) -> Sequence[Any]:
        return self.job_results.get(batch_job_name, [])
    
    def health_check(self) -> bool:
        return True


def test_batch_job_tracker_add_and_get(tmp_path: Path) -> None:
    """Test adding and retrieving job metadata."""
    tracking_file = tmp_path / "jobs.json"
    tracker = BatchJobTracker(tracking_file)
    
    metadata = BatchJobMetadata(
        provider_name="dummy",
        job_name="job-123",
        subject="Geography",
        filename="gcse-geography.md",
        batch_index=0,
        issue_ids=[1, 2, 3],
        created_at="2024-01-01T00:00:00Z",
        status="pending",
    )
    
    tracker.add_job(metadata)
    
    # Retrieve the job
    retrieved = tracker.get_job("job-123")
    assert retrieved is not None
    assert retrieved.job_name == "job-123"
    assert retrieved.subject == "Geography"
    assert retrieved.batch_index == 0
    assert retrieved.issue_ids == [1, 2, 3]


def test_batch_job_tracker_update_status(tmp_path: Path) -> None:
    """Test updating job status."""
    tracking_file = tmp_path / "jobs.json"
    tracker = BatchJobTracker(tracking_file)
    
    metadata = BatchJobMetadata(
        provider_name="dummy",
        job_name="job-123",
        subject="Geography",
        filename="gcse-geography.md",
        batch_index=0,
        issue_ids=[1, 2, 3],
        created_at="2024-01-01T00:00:00Z",
        status="pending",
    )
    
    tracker.add_job(metadata)
    tracker.update_job_status("job-123", "completed")
    
    retrieved = tracker.get_job("job-123")
    assert retrieved.status == "completed"


def test_batch_job_tracker_get_pending_jobs(tmp_path: Path) -> None:
    """Test retrieving only pending jobs."""
    tracking_file = tmp_path / "jobs.json"
    tracker = BatchJobTracker(tracking_file)
    
    tracker.add_job(BatchJobMetadata(
        provider_name="dummy",
        job_name="job-1",
        subject="Geography",
        filename="gcse-geography.md",
        batch_index=0,
        issue_ids=[1],
        created_at="2024-01-01T00:00:00Z",
        status="pending",
    ))
    
    tracker.add_job(BatchJobMetadata(
        provider_name="dummy",
        job_name="job-2",
        subject="Geography",
        filename="gcse-geography.md",
        batch_index=1,
        issue_ids=[2],
        created_at="2024-01-01T00:00:00Z",
        status="completed",
    ))
    
    pending = tracker.get_pending_jobs()
    assert len(pending) == 1
    assert pending[0].job_name == "job-1"


def test_batch_job_tracker_persists_to_file(tmp_path: Path) -> None:
    """Test that tracker persists data to JSON file."""
    tracking_file = tmp_path / "jobs.json"
    tracker = BatchJobTracker(tracking_file)
    
    metadata = BatchJobMetadata(
        provider_name="dummy",
        job_name="job-123",
        subject="Geography",
        filename="gcse-geography.md",
        batch_index=0,
        issue_ids=[1, 2, 3],
        created_at="2024-01-01T00:00:00Z",
        status="pending",
    )
    
    tracker.add_job(metadata)
    
    # Create new tracker with same file
    tracker2 = BatchJobTracker(tracking_file)
    retrieved = tracker2.get_job("job-123")
    
    assert retrieved is not None
    assert retrieved.job_name == "job-123"


def test_batch_orchestrator_process_batch_response_validates_correctly(tmp_path: Path) -> None:
    """Test that batch response processing validates correctly."""
    
    # Create a test CSV report
    report_path = tmp_path / "language-check-report.csv"
    report_path.write_text(
        "Subject,Filename,Page,Rule ID,Type,Issue,Message,Suggestions,Highlighted Context,Pass Code\n"
        "Geography,gcse-geography.md,1,TYPO,misspelling,teh,Possible spelling mistake,the,the **teh** quick,LT\n"
        "Geography,gcse-geography.md,2,GRAMMAR,grammar,are,Grammar error,is,they **are** here,LT\n"
        "Geography,gcse-geography.md,3,PUNCT,punctuation,.,Missing period,.,end of sentence**.**,LT\n"
    )
    
    # Create the markdown file that data_loader expects
    markdown_dir = tmp_path / "Documents" / "Geography" / "markdown"
    markdown_dir.mkdir(parents=True, exist_ok=True)
    markdown_file = markdown_dir / "gcse-geography.md"
    markdown_file.write_text("# Test Geography Document\n\nSome content here.")
    
    # Change to tmp_path so load_issues can find the Documents/ directory
    original_dir = os.getcwd()
    try:
        os.chdir(tmp_path)
        
        tracker = BatchJobTracker(tmp_path / "test_jobs.json")
        state = CategoriserState(tmp_path / "test_state.json")
        orchestrator = BatchOrchestrator(
            llm_service=LLMService([]),
            tracker=tracker,
            state=state,
            batch_size=10,
        )
        
        metadata = BatchJobMetadata(
            provider_name="dummy",
            job_name="job-123",
            subject="Geography",
            filename="gcse-geography.md",
            batch_index=0,
            issue_ids=[0, 1, 2],  # Use 0-based IDs as assigned by data_loader
            created_at="2024-01-01T00:00:00Z",
            status="pending",
        )
        
        # Valid response
        response = [
            {
                "issue_id": 0,
                "error_category": "SPELLING_ERROR",
                "confidence_score": 95,
                "reasoning": "Clear typo",
            },
            {
                "issue_id": 1,
                "error_category": "ABSOLUTE_GRAMMATICAL_ERROR",
                "confidence_score": 90,
                "reasoning": "Grammar issue",
            },
        ]
        
        results = orchestrator._process_batch_response(response, metadata, report_path)
        
        assert len(results) == 2
        # Check that merged results have all fields
        assert results[0]["issue_id"] == 0
        assert results[0]["error_category"] == "SPELLING_ERROR"
        assert results[0]["page_number"] == 1
        assert results[0]["issue"] == "teh"
        assert results[0]["highlighted_context"] == "the **teh** quick"
        assert results[0]["pass_code"] == "LTC"  # Should be set to LTC
        
        assert results[1]["issue_id"] == 1
        assert results[1]["error_category"] == "ABSOLUTE_GRAMMATICAL_ERROR"
    
    finally:
        os.chdir(original_dir)


def test_batch_orchestrator_process_batch_response_filters_invalid(tmp_path: Path) -> None:
    """Test that batch response processing filters out invalid entries."""
    
    # Create a test CSV report
    report_path = tmp_path / "language-check-report.csv"
    report_path.write_text(
        "Subject,Filename,Page,Rule ID,Type,Issue,Message,Suggestions,Highlighted Context,Pass Code\n"
        "Geography,gcse-geography.md,1,TYPO,misspelling,teh,Possible spelling mistake,the,the **teh** quick,LT\n"
        "Geography,gcse-geography.md,2,GRAMMAR,grammar,are,Grammar error,is,they **are** here,LT\n"
    )
    
    # Create the markdown file that data_loader expects
    markdown_dir = tmp_path / "Documents" / "Geography" / "markdown"
    markdown_dir.mkdir(parents=True, exist_ok=True)
    markdown_file = markdown_dir / "gcse-geography.md"
    markdown_file.write_text("# Test Geography Document\n\nSome content here.")
    
    # Change to tmp_path so load_issues can find the Documents/ directory
    original_dir = os.getcwd()
    try:
        os.chdir(tmp_path)
        
        tracker = BatchJobTracker(tmp_path / "test_jobs.json")
        state = CategoriserState(tmp_path / "test_state.json")
        orchestrator = BatchOrchestrator(
            llm_service=LLMService([]),
            tracker=tracker,
            state=state,
            batch_size=10,
        )
        
        metadata = BatchJobMetadata(
            provider_name="dummy",
            job_name="job-123",
            subject="Geography",
            filename="gcse-geography.md",
            batch_index=0,
            issue_ids=[0, 1],  # Use 0-based IDs
            created_at="2024-01-01T00:00:00Z",
            status="pending",
        )
        
        # Response with valid, missing fields, and wrong ID
        response = [
            {
                "issue_id": 0,
                "error_category": "SPELLING_ERROR",
                "confidence_score": 95,
                "reasoning": "Clear typo",
            },
            {
                "issue_id": 1,
                # Missing error_category
                "confidence_score": 90,
                "reasoning": "Grammar issue",
            },
            {
                "issue_id": 999,  # Not in batch
                "error_category": "GRAMMAR_ERROR",
                "confidence_score": 90,
                "reasoning": "Wrong batch",
            },
        ]
        
        results = orchestrator._process_batch_response(response, metadata, report_path)
        
        # Only first entry should be valid
        assert len(results) == 1
        assert results[0]["issue_id"] == 0
    
    finally:
        os.chdir(original_dir)


def test_batch_orchestrator_process_batch_response_handles_non_list(tmp_path: Path) -> None:
    """Test that non-list responses are handled gracefully."""
    
    # Create a minimal test CSV report
    report_path = tmp_path / "language-check-report.csv"
    report_path.write_text(
        "Subject,Filename,Page,Rule ID,Type,Issue,Message,Suggestions,Highlighted Context,Pass Code\n"
        "Geography,gcse-geography.md,1,TYPO,misspelling,teh,Possible spelling mistake,the,the **teh** quick,LT\n"
    )
    
    tracker = BatchJobTracker(tmp_path / "test_jobs.json")
    state = CategoriserState(tmp_path / "test_state.json")
    orchestrator = BatchOrchestrator(
        llm_service=LLMService([]),
        tracker=tracker,
        state=state,
        batch_size=10,
    )
    
    metadata = BatchJobMetadata(
        provider_name="dummy",
        job_name="job-123",
        subject="Geography",
        filename="gcse-geography.md",
        batch_index=0,
        issue_ids=[0, 1],
        created_at="2024-01-01T00:00:00Z",
        status="pending",
    )
    
    # Non-list response
    response = {"error": "Invalid format"}
    
    results = orchestrator._process_batch_response(response, metadata, report_path)
    
    assert len(results) == 0
