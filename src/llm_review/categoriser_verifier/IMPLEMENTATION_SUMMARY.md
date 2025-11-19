# Categoriser Verifier Module - Implementation Summary

## Overview

Successfully created a new `categoriser_verifier` module at `/workspaces/WjecDocumentScraper/src/llm_review/categoriser_verifier/` that performs a second-pass LLM review over the output from the `llm_categoriser` module.

## Module Structure

### Created Files

1. **`__init__.py`** - Package initialization
2. **`__main__.py`** - Module entry point
3. **`config.py`** - Configuration dataclass (`VerifierConfiguration`)
4. **`cli.py`** - Command-line interface with argument parsing
5. **`runner.py`** - Main workflow orchestrator (`VerifierRunner`)
6. **`prompt_factory.py`** - Prompt building using templates
7. **`persistence.py`** - Aggregated CSV output handler (`VerifierPersistenceManager`)
8. **`data_loader.py`** - Custom CSV parser for categorised report format
9. **`README.md`** - Comprehensive documentation

### Test File

- **`tests/test_categoriser_verifier.py`** - Unit tests covering configuration, persistence, prompts, and runner (7 tests, all passing)

## Key Design Decisions

### 1. Input Format Handling

The categorised report has a different structure than the raw language check report:
- **Columns**: `Subject, Filename, issue_id, page_number, issue, highlighted_context, pass_code, error_category, confidence_score, reasoning`
- **Enum Handling**: CSV contains enum values as `ErrorCategory.VALUE` strings, which the loader parses to proper enum values
- **Missing Fields**: Original detection fields (rule_id, message, etc.) are replaced with placeholder values since they're not in the categorised CSV

### 2. Prompt Reuse

- **System Prompt**: Uses the new `system_categoriser_verifier` template (provided as attachment)
- **User Prompt**: Reuses `user_language_tool_categoriser.md` from llm_categoriser
- Both prompts are rendered with the same context structure

### 3. Output Format

Unlike `llm_categoriser` which writes per-document CSVs, the verifier writes a single aggregated CSV:
- **Path**: `Documents/verified-llm-categorised-language-check-report.csv`
- **Columns**: Includes `subject` and `filename` columns to identify source documents
- **Accumulation**: Results are accumulated in memory during the run and written atomically at the end

### 4. State Management

- Uses the same state management infrastructure as `llm_categoriser`
- **State File**: `data/verifier_state.json`
- Supports `--force` flag to reprocess all batches

## Usage Examples

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
# Custom batch size and paths
python -m src.llm_review.categoriser_verifier \
  --batch-size 5 \
  --from-report Documents/custom-input.csv \
  --output Documents/custom-output.csv

# Force reprocessing
python -m src.llm_review.categoriser_verifier --force

# Dry run
python -m src.llm_review.categoriser_verifier --dry-run
```

## Environment Variables

- `VERIFIER_BATCH_SIZE` - Default: 10
- `VERIFIER_MAX_RETRIES` - Default: 2
- `VERIFIER_STATE_FILE` - Default: `data/verifier_state.json`
- `VERIFIER_LOG_RESPONSES` - Set to `true`/`1` to log raw LLM responses
- `VERIFIER_LOG_DIR` - Default: `data/verifier_responses`
- Plus standard LLM environment variables (GEMINI_*, LLM_PRIMARY, etc.)

## Testing

All tests pass successfully:
```bash
uv run pytest tests/test_categoriser_verifier.py -v
```

Output:
```
7 passed in 0.24s
```

## Validation

Dry run tested successfully with Art-and-Design subject:
```bash
uv run python -m src.llm_review.categoriser_verifier --dry-run --subjects "Art-and-Design"
```

Results:
- Loaded 7 documents with 91 total issues
- Created 13 batches
- Successfully parsed categorised CSV format
- Correctly mapped to markdown files
- Validated batch creation and page context loading

## Integration with Existing Workflow

The complete workflow is now:

1. **Language Check** → `Documents/language-check-report.csv`
   ```bash
   python main.py --language-check
   ```

2. **LLM Categoriser** → Per-document CSVs + `Documents/llm_categorised-language-check-report.csv`
   ```bash
   python -m src.llm_review.llm_categoriser
   ```

3. **Categoriser Verifier** → `Documents/verified-llm-categorised-language-check-report.csv`
   ```bash
   python -m src.llm_review.categoriser_verifier
   ```

## Architecture Alignment

The module follows the same architectural patterns as `llm_categoriser`:
- Extends `ReviewConfiguration` base class
- Uses core infrastructure (`batcher`, `state_manager`, `document_loader`)
- Implements the same retry and validation logic
- Supports batch API operations (could be extended if needed)
- Maintains compatibility with the prompt template system

## Notes

1. **Filename Extension Handling**: The runner automatically converts `.csv` filenames in the categorised report to `.md` when looking up markdown files
2. **Placeholder Values**: Since the categorised CSV lacks original detection fields, placeholder values (`rule_id="VERIFIER_REVIEW"`, etc.) are used to satisfy model validation
3. **Error Category Parsing**: Special handling to strip `ErrorCategory.` prefix from enum string values in the CSV
4. **Memory Usage**: All results are accumulated in memory before writing (acceptable given the relatively small size of the filtered dataset)

## Future Enhancements

Potential improvements:
1. Add batch API support (similar to llm_categoriser)
2. Implement streaming CSV writes for large datasets
3. Add parallel processing for multiple documents
4. Create comparison reports between categoriser and verifier outputs
5. Add confidence score trend analysis
