"""Batch orchestrator for LLM proofreading using Gemini Batch API.

This module provides functionality to create and retrieve batch jobs for
asynchronous processing of proofreading issues through the Gemini batch API.
"""

from __future__ import annotations

from pathlib import Path

from src.llm.service import LLMService

from ..core.batch_orchestrator import BatchOrchestrator
from ..core.state_manager import StateManager
from .config import ProofreaderConfiguration
from .data_loader import load_proofreader_issues
from .persistence import save_proofreader_results
from .prompt_factory import build_prompts


class ProofreaderBatchOrchestrator(BatchOrchestrator):
    """Orchestrates batch processing for proofreader."""

    def __init__(
        self,
        llm_service: LLMService,
        state: StateManager,
        config: ProofreaderConfiguration,
    ):
        """Initialize the orchestrator.

        Args:
            llm_service: LLM service for making batch API calls
            state: State manager for tracking progress
            config: Configuration for the proofreader
        """
        super().__init__(llm_service, state, config)

    def _load_issues(self):
        """Load issues using proofreader-specific loader."""
        return load_proofreader_issues(
            self.config.input_csv_path,
            subjects=self.config.subjects,
            documents=self.config.documents,
        )

    def _build_batch_prompts(self, batch):
        """Build prompts for a batch."""
        return build_prompts(batch)

    def _save_results(self, output_path: Path, results):
        """Save proofreader results."""
        save_proofreader_results(
            output_path,
            results,
            columns=self.config.output_csv_columns,
        )
