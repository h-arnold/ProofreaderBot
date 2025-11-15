**LLM Categoriser – Detailed Implementation Blueprint**

- **Scope**: Build a standalone categoriser that ingests `Documents/language-check-report.csv`, batches issues per document, prompts an LLM (via templates in `src/prompt/promptFiles/`) with per-batch tables and page context, retries malformed responses, and stores JSON outputs per document under `Documents/<subject>/document_reports/`.
- **Tech Constraints**: Stay single-threaded for API requests; respect provider-specific minimum request intervals; default batch size 10 (env/CLI override); maximum two retries on JSON parse/validation failure per batch; persistence happens per batch (redo the batch if interrupted).
- **Primary Dependencies**: `src/language_check.language_issue.LanguageIssue`, `src.utils.page_utils.extract_pages_text`, `src.prompt.render_prompt.render_template`, `src.llm.provider_registry.create_provider_chain`, `src.llm.service.LLMService`, `src.models.LlmLanguageIssue`/`ErrorCategory`.

---

### Workflow Overview

1. **Load issues**: Parse the LanguageTool CSV report into `LanguageIssue` objects grouped by subject and filename.
2. **Batch issues**: Slice each document’s issues into manageable batches (default 10). For every batch, collect the relevant page snippets from the Markdown source so the LLM gets only the necessary context.
3. **Render prompts**: Build a two-part prompt (system + user) using `language_tool_categoriser.md` (with partials `llm_reviewer_system_prompt.md` and `authoritative_sources.md`) that:
   - Introduces the subject and document being reviewed.
   - Presents the batch as a Markdown table mirroring the CSV columns.
   - Appends a “Page context” section listing the raw Markdown for each referenced page.
4. **Send to LLM**: Use `LLMService` to call the configured provider (chat or batch endpoint). Enforce provider min-request intervals to respect quotas.
5. **Validate output**: Parse the returned JSON, repair it when needed, and validate each record against `LlmLanguageIssue`. On failure, isolate the problematic issues and re-ask the provider (up to two retries). Any remaining failures are logged and skipped.
6. **Persist results**: Write valid responses into `Documents/<Subject>/document_reports/<filename>.json`, grouped by page (`"page_5": [ ... ]`). Track completed batches in a state file so restarts skip successful work unless `--force` is used.
7. **Manual testing**: Optional `--emit-batch-payload` flag writes batch payloads to `data/` and exits, enabling manual submission to provider batch consoles.

---

### Error Categories

The LLM must classify each issue into one of these enums (defined in `src/models/enums.py`):

- `PARSING_ERROR`: Mechanical or tokenisation mistakes such as missing hyphens (`privacyfocused`) or accidental concatenations.
- `SPELLING_ERROR`: Genuine misspellings or the wrong lexical choice given context (e.g., “their” vs “there”).
- `ABSOLUTE_GRAMMATICAL_ERROR`: Definite grammatical violations, including non-UK spelling variants that conflict with policy (“organize” vs “organise”).
- `POSSIBLE_AMBIGUOUS_GRAMMATICAL_ERROR`: Grammatically debatable constructions that may be awkward or non-standard rather than strictly wrong.
- `STYLISTIC_PREFERENCE`: Stylistic suggestions where the original text is acceptable (“in order to” vs “to”).
- `FALSE_POSITIVE`: Legitimate text flagged incorrectly (specialist terminology, proper nouns, foreign-language usage, etc.).

Each record also carries a `confidence_score` (0–100) and a single-sentence `reasoning` justification referencing authoritative sources or contextual cues.

---

### Expected Output Structure

The categoriser writes one JSON file per document. Example (trimmed for brevity):

```json
{
  "page_5": [
    {
      "rule_from_tool": "COMMA_COMPOUND_SENTENCE",
      "type_from_tool": "uncategorized",
      "message_from_tool": "Use a comma before ‘and’...",
      "suggestions_from_tool": [", and"],
      "context_from_tool": "...they are then used in marking the work...",
      "error_category": "POSSIBLE_AMBIGUOUS_GRAMMATICAL_ERROR",
      "confidence_score": 68,
      "reasoning": "Sentence is understandable without the comma; optional stylistic choice."
    }
  ],
  "page_6": [
    {
      "rule_from_tool": "EN_COMPOUNDS_USER_FRIENDLY",
      "type_from_tool": "misspelling",
      "message_from_tool": "This word is normally spelled with a hyphen.",
      "suggestions_from_tool": ["user-friendly"],
      "context_from_tool": "...made more user friendly?",
      "error_category": "PARSING_ERROR",
      "confidence_score": 90,
      "reasoning": "Hyphenation aligns with Collins Dictionary for compound adjective." 
    }
  ]
}
```

Notes:
- Keys are always `"page_<n>"` where `<n>` is the numeric page index.
- `suggestions_from_tool` is stored as a list (even if one suggestion was provided).
- Multiple issues per page append to that page’s array.
- If a batch produced no valid outputs (after retries), it is omitted and the CLI logs which rows need manual handling.

---

### Core Modules & Responsibilities

- **`llm_categoriser/data_loader.py`**
  - Parse CSV into `LanguageIssue` objects grouped by `(subject, filename)`.
  - Filters for subject/document subsets; validates corresponding Markdown exists.
  - Contract: `load_issues(report_path: Path, *, subjects: set[str] | None, documents: set[str] | None) -> dict[DocumentKey, list[LanguageIssue]]`.

- **`llm_categoriser/batcher.py`**
  - Chunk issues per document (`batch_size`).
  - Deduplicate page numbers, fetch page snippets via `extract_pages_text`, and create Markdown tables using a helper from `report_utils.py`.
  - Contract: `iter_batches(issues: list[LanguageIssue], batch_size: int) -> Iterable[Batch]` where each `Batch` contains `subject`, `filename`, `index`, `issues`, `page_context`, `markdown_table`.

- **`llm_categoriser/prompt_factory.py`**
  - Render prompts using the revised `language_tool_categoriser.md` template (ensure placeholders for subject, filename, issue table, and page context remain in sync with this README).
  - Contract: `build_prompts(batch: Batch) -> list[str]` returning `[system_prompt, user_prompt]`.

- **`llm/json_utils.py` (new)**
  - Shared JSON extraction/repair using `json-repair` plus validation helpers.
  - Providers (e.g., `GeminiLLM`) delegate to this utility when `filter_json=True`.

- **`llm_categoriser/runner.py`**
  - Orchestrate the workflow: call providers, apply retries, validate `LlmLanguageIssue`, and direct successful results to persistence.
  - Respects provider min request intervals and logs quota fallbacks.

- **`llm_categoriser/persistence.py`**
  - Write per-document JSON atomically; merge batches when rerunning without `--force`.

- **`llm_categoriser/state.py`**
  - Maintain a JSON state file (default `data/llm_categoriser_state.json`) tracking completed batches (`"<subject>/<filename>#<batch_index>"`).

- **`llm_categoriser/cli.py` & `__main__`**
  - Provide CLI entrypoint with options for subject/document selection, batch size, retry count, provider ordering, state management, manual payload emission, and batch endpoint usage.

---

### Provider Adjustments

- Extend provider wrappers (starting with Gemini) to honour a `min_request_interval` to respect provider rate limits.
- Centralise JSON parsing in `llm/json_utils.py` so every provider behaves consistently.
- Ensure provider errors carry context for runner logging and retry decisions.
- When templates in `src/prompt/promptFiles/` change, adjust `prompt_factory.py` and related tests to keep placeholder names consistent.

---

### Retry & Error Handling

1. Parse provider response via shared JSON utility.
2. Validate each entry with `LlmLanguageIssue`.
3. If some records fail validation, rebuild a reduced prompt with only those issues and retry (max two retries). Successful records are kept; failed ones after retries are logged and skipped.
4. State file is only updated after a batch fully succeeds to avoid skipping unfinished work on rerun.

---

### Persistence & Output

- Results stored in `Documents/<Subject>/document_reports/<filename>.json`.
- Each write is atomic (temporary file + replace).
- Existing files are merged unless `--force` is set.
- Optional state/resume support prevents duplicate calls when restarting the CLI.

---

### CLI & Configuration

- Key options: `--subjects`, `--documents`, `--from-report`, `--batch-size`, `--max-retries`, `--state-file`, `--force`, `--use-batch-endpoint`, `--emit-batch-payload`, `--provider`, `--dotenv`, `--dry-run`.
- Environment overrides: `LLM_CATEGORISER_BATCH_SIZE`, `LLM_CATEGORISER_MAX_RETRIES`, `LLM_CATEGORISER_STATE_FILE`, provider-specific min interval vars (e.g., `GEMINI_MIN_REQUEST_INTERVAL`).

---

### Testing Strategy

- Create targeted tests in `tests/llm_categoriser/` covering loaders, batching, prompt generation, retry logic, persistence, state tracking, and CLI behaviour.
- Update provider tests to confirm min-interval enforcement and shared JSON parsing.

---

### Implementation Sequence

1. Update `.gitignore` for state/payload files.
2. Implement shared JSON utilities and provider rate limiting; add unit tests.
3. Add Markdown table helper in `report_utils.py`.
4. Scaffold new categoriser modules.
5. Revise prompt template and implement prompt factory.
6. Build data loader and batcher with tests.
7. Implement state tracker, persistence, runner, and tests using fake provider responses.
8. Implement CLI and associated tests.
9. Run `uv run pytest -q`; perform manual `--emit-batch-payload` check.
10. Update documentation (README, CHANGES if needed).

---

### Risks & Mitigations

- Control token usage by limiting page context to referenced pages; consider optional guard on context length.
- Deduplicate CSV issues before batching to avoid redundant prompts.
- Defer state updates until after successful writes to handle retries cleanly.
- Offer manual payload emission for troubleshooting provider issues.

---

### Documentation & Follow-up

- Keep this README aligned with any future changes to prompt structure or CLI options.
- Document state file format for resume functionality.
- Future enhancement: optional importer for externally processed batch results.
- Highlight single-threaded design and rate limiting rationale for maintainers.

This blueprint consolidates the agreed constraints (single-threaded processing, provider-specific rate limiting, targeted retries, batch-level persistence) and lays out the module responsibilities, contracts, and sequencing required to implement the LLM categoriser successfully.