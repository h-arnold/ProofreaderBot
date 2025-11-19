"""Orchestrate the categoriser verifier workflow with retries and validation.

This module coordinates the verification process: loading categorised issues,
batching, prompting the LLM, validating responses, handling retries, and
persisting results to an aggregated CSV.

Key differences from llm_categoriser runner:
    - Uses VerifierPersistenceManager for aggregated output
    - Writes to single CSV at end rather than per-document CSVs
    - Expects input from llm_categorised-language-check-report.csv
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any

from pydantic import ValidationError

from src.llm.service import LLMService
from src.models import LanguageIssue, PassCode

from ..core.batcher import Batch
from ..core.state_manager import StateManager
from .config import VerifierConfiguration
from .persistence import VerifierPersistenceManager
from .prompt_factory import build_prompts


class VerifierRunner:
    """Orchestrates the categoriser verifier workflow."""

    def __init__(
        self,
        llm_service: LLMService,
        state: StateManager,
        *,
        batch_size: int = 10,
        max_retries: int = 2,
        log_raw_responses: bool | None = None,
        log_response_dir: Path | None = None,
        fail_on_quota: bool = True,
    ):
        """Initialize the runner.

        Args:
            llm_service: LLM service for making API calls
            state: State manager for tracking progress
            batch_size: Number of issues per batch
            max_retries: Maximum retry attempts for failed validations
            log_raw_responses: Whether to log raw LLM responses (None = read from env)
            log_response_dir: Directory for response logs (None = use default)
            fail_on_quota: Whether to abort on quota exhaustion
        """
        # Handle environment variable defaults
        if log_raw_responses is None:
            env_flag = os.environ.get("VERIFIER_LOG_RESPONSES", "")
            log_raw_responses = env_flag.strip().lower() in {"1", "true", "yes", "on"}

        if log_response_dir is None:
            log_response_dir = Path(
                os.environ.get("VERIFIER_LOG_DIR", "data/verifier_responses")
            )

        # Create a configuration object
        self.config = VerifierConfiguration(
            input_csv_path=Path("Documents/llm_categorised-language-check-report.csv"),
            output_base_dir=Path("Documents"),
            output_subdir="verifier_reports",
            aggregated_output_path=Path(
                "Documents/verified-llm-categorised-language-check-report.csv"
            ),
            batch_size=batch_size,
            max_retries=max_retries,
            state_file=Path("data/verifier_state.json"),
            subjects=None,
            documents=None,
            llm_provider=None,
            fail_on_quota=fail_on_quota,
            log_raw_responses=log_raw_responses,
            log_response_dir=log_response_dir,
            output_csv_columns=[
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
            ],
        )

        self.llm_service = llm_service
        self.state = state
        self.persistence = VerifierPersistenceManager(self.config)

        if self.config.log_raw_responses:
            print(
                f"Raw response logging enabled -> {self.config.log_response_dir} (subject folders will be created automatically)"
            )

    def run(
        self,
        report_path: Path,
        *,
        subjects: set[str] | None = None,
        documents: set[str] | None = None,
        force: bool = False,
        dry_run: bool = False,
    ) -> dict[str, Any]:
        """Run the verification workflow.

        Args:
            report_path: Path to llm_categorised-language-check-report.csv
            subjects: Optional subject filter
            documents: Optional document filter
            force: If True, reprocess all batches (ignore state)
            dry_run: If True, only validate data loading (don't call LLM)

        Returns:
            Summary statistics dictionary
        """
        # Update config with runtime parameters
        self.config.input_csv_path = report_path
        self.config.subjects = subjects
        self.config.documents = documents

        # Clear accumulated results from any previous run
        self.persistence.clear()

        # Load issues using custom categorised loader
        from .data_loader import load_categorised_issues

        print(f"Loading issues from {report_path}...")
        grouped_issues = load_categorised_issues(
            report_path,
            subjects=subjects,
            documents=documents,
        )

        if not grouped_issues:
            print("No issues found matching the filters")
            return {"total_documents": 0, "total_batches": 0, "total_issues": 0}

        print(f"Loaded {len(grouped_issues)} document(s) with issues")

        total_batches = 0
        total_issues = 0
        processed_batches = 0
        skipped_batches = 0

        # Process each document
        from ..core.batcher import iter_batches

        for key, issues in grouped_issues.items():
            print(f"\nProcessing {key} ({len(issues)} issues)...")
            total_issues += len(issues)

            # Get Markdown path - convert .csv filename to .md
            markdown_filename = key.filename
            if markdown_filename.endswith(".csv"):
                markdown_filename = markdown_filename[:-4] + ".md"
            markdown_path = (
                Path("Documents") / key.subject / "markdown" / markdown_filename
            )

            # Clear state if force mode
            if force:
                self.state.clear_document(key)

            # Process batches for this document
            for batch in iter_batches(
                issues,
                self.config.batch_size,
                markdown_path,
                subject=key.subject,
                filename=key.filename,
            ):
                total_batches += 1

                # Check if already completed
                if not force and self.state.is_batch_completed(key, batch.index):
                    print(f"  Batch {batch.index}: Already completed (skipping)")
                    skipped_batches += 1
                    # Still need to load the results from state if they exist
                    # For now, we'll just skip - state management needs enhancement
                    continue

                if dry_run:
                    print(f"  Batch {batch.index}: Dry run (not calling LLM)")
                    continue

                # Process the batch
                success = self._process_batch(key, batch)
                if success:
                    processed_batches += 1
                    self.state.mark_batch_completed(key, batch.index, len(issues))

        # Write aggregated results to CSV
        if not dry_run and self.persistence.aggregated_results:
            output_path = self.config.aggregated_output_path or Path(
                "Documents/verified-llm-categorised-language-check-report.csv"
            )
            self.persistence.write_aggregated_results(output_path)

        # Print summary
        print("\n" + "=" * 60)
        print("Verification Summary")
        print("=" * 60)
        print(f"Total documents: {len(grouped_issues)}")
        print(f"Total issues: {total_issues}")
        print(f"Total batches: {total_batches}")
        print(f"Processed batches: {processed_batches}")
        print(f"Skipped batches: {skipped_batches}")
        print("=" * 60)

        return {
            "total_documents": len(grouped_issues),
            "total_batches": total_batches,
            "total_issues": total_issues,
            "processed_batches": processed_batches,
            "skipped_batches": skipped_batches,
        }

    def _process_batch(self, key, batch: Batch) -> bool:
        """Process a single batch with retries.

        Returns:
            True if batch was successfully processed, False otherwise
        """
        print(f"  Batch {batch.index}: {len(batch.issues)} issues")

        for attempt in range(1, self.config.max_retries + 1):
            try:
                # Build prompts
                prompts = build_prompts(batch)

                # Call LLM
                response = self._call_llm(prompts, key, batch.index, attempt)
                if response is None:
                    return False

                # Log raw response if enabled
                if self.config.log_raw_responses:
                    self._log_response(key, batch.index, attempt, response)

                # Validate response
                validated_results, failed_ids, error_messages = self.validate_response(
                    response, batch.issues
                )

                if not failed_ids:
                    # Success - add to aggregated results
                    self.persistence.add_batch_results(key, validated_results)
                    print(f"    ✓ Validated {len(validated_results)} issues")
                    return True
                else:
                    # Some issues failed validation
                    print(
                        f"    ✗ Validation failed for {len(failed_ids)} issues (attempt {attempt}/{self.config.max_retries})"
                    )
                    if attempt < self.config.max_retries:
                        print("    Retrying...")
                    else:
                        print("    Max retries reached, skipping batch")
                        return False

            except Exception as e:
                print(f"    Error processing batch: {e}")
                if attempt < self.config.max_retries:
                    print("    Retrying...")
                else:
                    print("    Max retries reached, skipping batch")
                    return False

        return False

    def build_prompts(self, batch: Batch) -> list[str]:
        """Build prompts for the LLM.

        Args:
            batch: Batch of issues to process

        Returns:
            List of prompts (system prompt, then user prompt)
        """
        return build_prompts(batch)

    def validate_response(
        self,
        response: Any,
        issues: list[LanguageIssue],
    ) -> tuple[list[dict[str, Any]], set[int], dict[object, list[str]]]:
        """Validate LLM response and return validated results, failed ids and error messages.

        Args:
            response: The raw LLM response
            issues: List of issues in the batch

        Returns:
            Tuple of (validated_results, failed_issue_ids, error_messages)
        """
        validated_results: list[dict[str, Any]] = []
        failed_issue_ids: set[int] = set(issue.issue_id for issue in issues)

        # Map of issue ids or 'batch_errors' to lists of messages
        error_messages: dict[object, list[str]] = {
            issue.issue_id: [] for issue in issues
        }
        error_messages.setdefault("batch_errors", [])

        # Only accept a top-level JSON array of objects from the LLM.
        if not isinstance(response, list):
            msg = "Expected top-level JSON array of objects"
            print(f"    Error: {msg}")
            error_messages.setdefault("batch_errors", []).append(msg)
            return validated_results, failed_issue_ids, error_messages

        # Get filename from first issue (all issues in a batch are from same document)
        filename = issues[0].filename if issues else ""

        if not response:
            msg = "Response is empty; no issues to validate"
            print(f"    Warning: {msg}")
            error_messages.setdefault("batch_errors", []).append(msg)
            return validated_results, failed_issue_ids, error_messages

        # Build a map of original issues indexed by issue_id
        issue_map = {issue.issue_id: issue for issue in issues}

        # Process the flat response list
        for issue_dict in response:
            # Only accept dictionaries
            if not isinstance(issue_dict, dict):
                warn = "Entry in response array is not a JSON object"
                print(f"    Warning: {warn}")
                error_messages.setdefault("batch_errors", []).append(warn)
                continue

            try:
                iid = (
                    issue_dict.get("issue_id") if isinstance(issue_dict, dict) else None
                )

                if iid is not None and iid in issue_map:
                    # Merge verifier results into the original issue
                    orig = issue_map[iid]
                    merged = {
                        "filename": orig.filename,
                        "rule_id": orig.rule_id,
                        "message": orig.message,
                        "issue_type": orig.issue_type,
                        "replacements": orig.replacements,
                        "context": orig.context,
                        "highlighted_context": orig.highlighted_context,
                        "issue": orig.issue,
                        "page_number": orig.page_number,
                        "issue_id": orig.issue_id,
                        "pass_code": PassCode.LTC,
                        # LLM fields (verified/updated)
                        "error_category": issue_dict.get("error_category"),
                        "confidence_score": issue_dict.get("confidence_score"),
                        "reasoning": issue_dict.get("reasoning"),
                    }
                    validated = LanguageIssue(**merged)
                else:
                    # Fall back to creating from full LLM response
                    validated = LanguageIssue.from_llm_response(
                        issue_dict, filename=filename
                    )
                validated_results.append(validated.model_dump())

                # If the LLM supplied an explicit issue_id, mark it as validated.
                if validated.issue_id >= 0:
                    failed_issue_ids.discard(validated.issue_id)

            except ValidationError as e:
                iid = (
                    issue_dict.get("issue_id") if isinstance(issue_dict, dict) else None
                )
                if iid is not None:
                    error_messages.setdefault(iid, []).append(str(e))
                else:
                    error_messages.setdefault("batch_errors", []).append(str(e))
                continue
            except Exception as e:
                iid = (
                    issue_dict.get("issue_id") if isinstance(issue_dict, dict) else None
                )
                if iid is not None:
                    error_messages.setdefault(iid, []).append(str(e))
                else:
                    error_messages.setdefault("batch_errors", []).append(str(e))
                continue

        if not validated_results:
            msg = "Response contained no valid issue objects"
            error_messages.setdefault("batch_errors", []).append(msg)

        return validated_results, failed_issue_ids, error_messages

    def _call_llm(self, prompts: list[str], key, batch_index: int, attempt: int):
        """Call LLM with filter_json=True for categoriser."""
        from src.llm.provider import LLMQuotaError

        try:
            return self.llm_service.generate(prompts, filter_json=True)
        except Exception as e:
            if isinstance(e, LLMQuotaError) and not self.config.fail_on_quota:
                print(f"    Quota exhausted (skipping batch): {e}")
                return None
            print(f"    LLM error: {e}")
            if self.config.fail_on_quota:
                raise
            return None

    def _log_response(self, key, batch_index: int, attempt: int, response: Any):
        """Log raw LLM response to disk."""
        import json
        from datetime import datetime, timezone

        log_dir = self.config.log_response_dir / key.subject
        log_dir.mkdir(parents=True, exist_ok=True)

        timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        log_file = (
            log_dir
            / f"{key.filename}_batch{batch_index}_attempt{attempt}_{timestamp}.json"
        )

        try:
            with open(log_file, "w", encoding="utf-8") as f:
                json.dump(response, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"    Warning: Failed to log response to {log_file}: {e}")
