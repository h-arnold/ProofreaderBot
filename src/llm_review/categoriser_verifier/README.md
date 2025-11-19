# Categoriser Verifier

A second-pass LLM review module that verifies and refines the categorisation of language issues produced by the `llm_categoriser` module.

## Overview

The `categoriser_verifier` module takes the aggregated output from `llm_categoriser` and performs a verification pass to:
- Validate categorisation decisions
- Correct misclassifications
- Update confidence scores
- Refine reasoning

## Key Differences from llm_categoriser

| Feature | llm_categoriser | categoriser_verifier |
|---------|----------------|---------------------|
| **Input** | `Documents/language-check-report.csv` | `Documents/llm_categorised-language-check-report.csv` |
| **Output** | Per-document CSVs in `Documents/<subject>/document_reports/` | Single aggregated CSV: `Documents/verified-llm-categorised-language-check-report.csv` |
| **System Prompt** | `system_language_tool_categoriser.md` | `system_categoriser_verifier` |
| **User Prompt** | `user_language_tool_categoriser.md` | `user_language_tool_categoriser.md` (reused) |
| **State File** | `data/llm_categoriser_state.json` | `data/verifier_state.json` |

## Usage

### Basic Usage

```bash
# Verify all categorised issues
python -m src.llm_review.categoriser_verifier
```

### Filtering

```bash
# Verify specific subjects
python -m src.llm_review.categoriser_verifier --subjects Geography History

# Verify specific documents
python -m src.llm_review.categoriser_verifier --documents gcse-geography.md
```

### Configuration

```bash
# Custom batch size
python -m src.llm_review.categoriser_verifier --batch-size 5

# Custom input/output paths
python -m src.llm_review.categoriser_verifier \
  --from-report Documents/custom-input.csv \
  --output Documents/custom-output.csv

# Force reprocessing (ignore state)
python -m src.llm_review.categoriser_verifier --force

# Dry run (validate data loading only)
python -m src.llm_review.categoriser_verifier --dry-run
```

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `VERIFIER_BATCH_SIZE` | `10` | Number of issues per batch |
| `VERIFIER_MAX_RETRIES` | `2` | Maximum retry attempts for failed validations |
| `VERIFIER_STATE_FILE` | `data/verifier_state.json` | Path to state file |
| `VERIFIER_LOG_RESPONSES` | `false` | Set to `true`/`1` to dump raw LLM responses |
| `VERIFIER_LOG_DIR` | `data/verifier_responses` | Directory for raw response logs |
| `GEMINI_MIN_REQUEST_INTERVAL` | `0` | Minimum seconds between Gemini requests |
| `GEMINI_MAX_RETRIES` | `0` | Number of retry attempts for 429 errors |
| `LLM_PRIMARY` | `gemini` | Primary LLM provider |
| `LLM_FALLBACK` | - | Fallback providers (comma-separated) |
| `LLM_FAIL_ON_QUOTA` | `true` | Exit on quota exhaustion |

## Architecture

The module follows the same architecture as `llm_categoriser` but with simplified output handling:

1. **Data Loading** (`core.document_loader`): Parse the categorised CSV and group issues by document
2. **Batching** (`core.batcher`): Chunk issues and fetch page context from Markdown files
3. **Prompt Building** (`prompt_factory`): Render prompts using templates with batch context
4. **LLM Calling** (`runner`): Orchestrate workflow with retries and validation
5. **Persistence** (`persistence`): Accumulate results and write single aggregated CSV
6. **State Management** (`core.state_manager`): Track completed batches for resume support

## Output Format

The output CSV includes the following columns:

- `subject`: Subject name (e.g., "Art-and-Design")
- `filename`: Document filename (e.g., "gcse-art-and-design.csv")
- `issue_id`: Unique issue identifier
- `page_number`: Page number in the source document
- `issue`: The flagged text
- `highlighted_context`: Context with the issue highlighted
- `pass_code`: Always `PassCode.LTC` (LanguageTool Check)
- `error_category`: Verified error category (enum value)
- `confidence_score`: Verified confidence score (0-100)
- `reasoning`: Verified reasoning for the categorisation

## Workflow Integration

Typical workflow:

1. Run language check:
   ```bash
   python main.py --language-check
   ```
   Output: `Documents/language-check-report.csv`

2. Run LLM categoriser:
   ```bash
   python -m src.llm_review.llm_categoriser
   ```
   Output: Per-document CSVs + aggregated `Documents/llm_categorised-language-check-report.csv`

3. Run categoriser verifier:
   ```bash
   python -m src.llm_review.categoriser_verifier
   ```
   Output: `Documents/verified-llm-categorised-language-check-report.csv`

## State Management

The verifier maintains state in `data/verifier_state.json` to support resuming interrupted runs:

- Tracks completed batches per document
- Allows `--force` to reprocess all batches
- State is persisted after each successful batch

## Error Handling

- **Validation Failures**: Retries up to `--max-retries` times
- **Quota Exhaustion**: Exits immediately if `--fail-on-quota` is set (default: true)
- **Network Errors**: Logs error and retries or skips batch depending on configuration
- **Invalid Responses**: Logs validation errors and retries or skips batch

## Logging

Enable raw response logging to inspect LLM outputs:

```bash
export VERIFIER_LOG_RESPONSES=true
python -m src.llm_review.categoriser_verifier
```

Responses are saved to `data/verifier_responses/<subject>/<filename>_batch<N>_attempt<M>_<timestamp>.json`

## Testing

```bash
# Run tests
uv run pytest tests/test_categoriser_verifier.py -v

# Run with coverage
uv run pytest tests/test_categoriser_verifier.py --cov=src.llm_review.categoriser_verifier
```

## Development

When modifying prompts:

1. Update `src/prompt/promptFiles/system_categoriser_verifier` for system prompt changes
2. User prompt is shared with `llm_categoriser` via `user_language_tool_categoriser.md`
3. Test prompt rendering: See `prompt_factory.build_prompts()` function

## See Also

- [llm_categoriser README](../llm_categoriser/README.md) - First-pass categorisation
- [ARCHITECTURE.md](../../../docs/ARCHITECTURE.md) - Overall architecture
- [LLM_PROVIDER_SPEC.md](../../../docs/LLM_PROVIDER_SPEC.md) - LLM provider documentation
