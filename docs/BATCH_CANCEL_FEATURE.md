# Batch Job Cancellation Feature

This document describes the batch job cancellation feature added to the WjecDocumentScraper project.

## Overview

The batch cancellation feature allows you to cancel pending batch jobs that are no longer needed. This is useful when:
- You've submitted jobs with incorrect parameters
- You need to stop processing to conserve API quota
- You want to re-submit jobs with different batch sizes
- You need to cancel large batch processing operations

## Implementation

The feature is implemented across three layers:

### 1. Provider Layer (GeminiLLM)

**File:** `src/llm/gemini_llm.py`

Added method:
```python
def cancel_batch_job(self, batch_job_name: str) -> None:
    """Cancel a pending batch job.
    
    Args:
        batch_job_name: The name of the batch job to cancel.
    
    Raises:
        LLMProviderError: If cancellation fails.
    """
```

This method calls the Google Gemini API's `batches.delete()` method to cancel the job.

### 2. Service Layer (LLMService)

**File:** `src/llm/service.py`

Added method:
```python
def cancel_batch_job(
    self,
    provider_name: str,
    batch_job_name: str,
) -> None:
    """Cancel a pending batch job.
    
    Args:
        provider_name: The name of the provider that created the batch job.
        batch_job_name: The batch job identifier returned from create_batch_job.
    
    Raises:
        ValueError: If provider not found.
        NotImplementedError: If provider doesn't support cancellation.
        LLMProviderError: If cancellation fails.
    """
```

This method provides a provider-agnostic interface for cancelling batch jobs.

### 3. Orchestrator Layer (BatchOrchestrator)

**File:** `src/llm_review/llm_categoriser/batch_orchestrator.py`

Added method:
```python
def cancel_batch_jobs(
    self,
    *,
    job_names: list[str] | None = None,
    cancel_all_pending: bool = False,
) -> dict[str, Any]:
    """Cancel batch jobs.
    
    Args:
        job_names: Optional list of specific job names to cancel
        cancel_all_pending: If True, cancel all pending jobs
        
    Returns:
        Summary statistics dictionary
    """
```

This method:
- Retrieves jobs from the tracker
- Filters by pending status
- Calls the LLM service to cancel each job
- Updates job status to "failed" with message "Cancelled by user"
- Reports summary statistics

### 4. CLI Layer

**File:** `src/llm_review/llm_categoriser/batch_cli.py`

Added subcommand: `batch-cancel`

Added function:
```python
def handle_batch_cancel(args: argparse.Namespace) -> int:
    """Handle batch-cancel subcommand."""
```

## CLI Usage

### Cancel All Pending Jobs

```bash
python -m src.llm_review.llm_categoriser batch-cancel --cancel-all-pending
```

Example output:
```
Using LLM provider(s): ['gemini']
Found 5 pending job(s) to cancel

Cancelling batch-abc123... (Geography/gcse-geography.md)
  Successfully cancelled
Cancelling batch-def456... (History/gcse-history.md)
  Successfully cancelled
...

============================================================
Summary:
  Cancelled: 5
  Failed to cancel: 0
  Skipped (not pending): 0
============================================================
```

### Cancel Specific Jobs

```bash
python -m src.llm_review.llm_categoriser batch-cancel --job-names batch-abc123 batch-def456
```

### Custom Tracking File

```bash
python -m src.llm_review.llm_categoriser batch-cancel --cancel-all-pending --tracking-file data/my_jobs.json
```

## Behavior

1. **Status Filter**: Only jobs with status "pending" are cancelled. Jobs that are "completed" or "failed" are skipped.

2. **Status Update**: When a job is successfully cancelled, its status in the tracking file is updated to "failed" with error_message set to "Cancelled by user".

3. **Error Handling**: If cancellation fails for a job, an error message is displayed and the cancellation continues for remaining jobs.

4. **API Call**: The feature uses the Google Gemini Batch API's `delete` method to cancel jobs on the server side.

## Testing

Tests have been added to ensure correct behavior:

### GeminiLLM Tests (`tests/test_gemini_batch.py`)
- `test_cancel_batch_job_calls_delete`: Verifies delete method is called
- `test_cancel_batch_job_raises_on_not_found`: Verifies error handling

### LLMService Tests (`tests/test_service_batch.py`)
- `test_cancel_batch_job_calls_provider`: Verifies delegation to provider
- `test_cancel_batch_job_raises_when_provider_not_found`: Verifies provider validation
- `test_cancel_batch_job_raises_when_provider_unsupported`: Verifies feature support check
- `test_cancel_batch_job_propagates_provider_error`: Verifies error propagation
- `test_cancel_batch_job_reports_events`: Verifies reporter integration

All tests pass successfully.

## Documentation Updates

Updated documentation files:
1. **docs/BATCH_API_USAGE.md**: Added `cancel_batch_job()` method documentation with examples
2. **docs/BATCH_ORCHESTRATOR_USAGE.md**: Added CLI usage examples for the `batch-cancel` command
3. **docs/BATCH_CANCEL_FEATURE.md** (this file): Comprehensive feature documentation

## Limitations

1. **Pending Jobs Only**: Can only cancel jobs with "pending" status. Completed or failed jobs cannot be cancelled.
2. **Provider Support**: Currently only implemented for Gemini provider. Other providers would need to implement the `cancel_batch_job()` method.
3. **No Confirmation**: The CLI does not ask for confirmation before cancelling (use with caution).
4. **Irreversible**: Once cancelled, jobs cannot be resumed or restarted. You must create new jobs.

## Future Enhancements

Potential improvements for future versions:
1. Add `--dry-run` flag to preview what would be cancelled
2. Add confirmation prompt for `--cancel-all-pending`
3. Support cancelling by subject or document filters
4. Add ability to cancel completed jobs (clean up server-side resources)
5. Implement for additional LLM providers (e.g., Mistral)

## Related Commands

- `batch-create`: Create new batch jobs
- `batch-fetch`: Fetch results from completed jobs
- `batch-list`: List all tracked jobs with status
- `batch-refresh-errors`: Update error details for failed jobs
