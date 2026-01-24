# WJEC Document Scraper

A command-line pipeline for bulk acquisition and multi-pass proofreading of WJEC GCSE "Made for Wales" PDF documents. The project automates document collection, conversion to Markdown, language checks, and LLM-assisted review so large document sets can be analysed consistently and at scale.

## What this tool does

- **Scrapes and downloads PDFs** from the WJEC qualification pages.
- **Normalises and organises files** into subject-specific folders.
- **Converts PDFs to Markdown** using high-fidelity converters (default: Marker).
- **Runs automated language checks** with LanguageTool to identify spelling and grammar issues.
- **Performs LLM-based review passes** to categorise issues, de-duplicate false positives, and catch contextual errors.
- **Exports structured outputs** (CSV reports) for auditing and analysis.

## Technology stack

The project combines conventional scraping and text processing with LLM-assisted review:

- **Python 3.12** runtime with `uv` for dependency management and execution.
- **Requests + BeautifulSoup** style HTML parsing for PDF discovery.
- **Marker** (default) or **Docling** for PDF-to-Markdown conversion with OCR support.
- **LanguageTool** via `language-tool-python` for rule-based spelling and grammar checks.
- **Gemini and Mistral APIs** for LLM-assisted categorisation and proofreading passes.
- **Pydantic models** (notably `LanguageIssue`) to validate and normalise issue payloads.
- **json-repair** integration to recover malformed JSON responses before validation.

## Multi-pass proofreading pipeline

The workflow is intentionally staged so each pass refines the results of the previous one:

1. **Acquisition pass**
   - Scrape subject pages and download linked PDFs into `Documents/<Subject>/`.
2. **Conversion pass**
   - Convert PDFs to Markdown, preserving layout cues and page markers for downstream processing.
3. **LanguageTool pass**
   - Run spelling/grammar checks and create a baseline issue list.
4. **LLM categorisation pass**
   - Use LLMs to filter false positives, classify issues, and prioritise review effort.
   - LLM outputs are repaired with `repair_json` before being parsed and validated.
   - The `LanguageIssue` model enforces required fields, normalises values, and rejects partial LLM payloads to keep the results consistent.
5. **LLM proofreading pass**
   - Review document text in small page chunks to catch contextual, consistency, and factual errors.
   - Outputs are validated against the same `LanguageIssue` schema to keep issue metadata aligned with earlier passes.
6. **Reporting pass**
   - Emit per-document CSV reports for analysis and aggregation.

This layered approach reduces noise from OCR artefacts while making the remaining issues easier to triage.

## Architecture at a glance

- **CLI entry point:** `main.py` (delegates to `src/cli`)
- **Scraper:** `src/scraper/__init__.py` (subject list, URL discovery, file naming)
- **Post-processing:** `src/postprocessing/__init__.py` (organises PDFs, converts to Markdown)
- **Converters:** `src/converters/converters.py` (Marker and Docling backends)
- **Language checking:** `src/language_check/language_check.py`
- **LLM review modules:** `src/llm_review/` (categoriser, proofreader, batch orchestration)
- **Reporting utilities:** `src/utils/page_utils.py`, `scripts/document_stats.py`

## Setup

Dependencies are managed with [uv](https://github.com/astral-sh/uv).

```bash
uv sync
```

## CLI usage

List available subjects:

```bash
uv run python main.py --list-subjects
```

Download all subjects:

```bash
uv run python main.py
```

Download selected subjects to a custom location:

```bash
uv run python main.py --subjects "Art and Design" French --root ./wjec-pdfs
```

Preview downloads without writing files:

```bash
uv run python main.py --subjects Geography --dry-run
```

## Post-processing downloads

The CLI can organise PDFs into `pdfs/`, convert them to `markdown/`, and extract images as needed:

- `--post-process` runs the organiser after downloading.
- `--post-process-only` skips downloading and processes existing PDFs.
- `--post-process-file <path>` converts a single PDF.
- `--post-process-workers N` caps concurrent subject processing.
- `--converter {marker,docling}` chooses the PDF-to-Markdown backend (default: `marker`).

Examples:

```bash
# Download and convert
uv run python main.py --subjects Geography --post-process

# Convert an existing folder
uv run python main.py --root Documents --post-process-only --converter marker

# Convert a single PDF
uv run python main.py --post-process-file Documents/Art-and-Design/sample.pdf
```

## LLM review tooling

The LLM review modules build on the LanguageTool output and the Markdown page markers. They support both live and batch modes, with resumable state tracking and per-document CSV outputs. See `docs/developer/LLM_REVIEW_MODULE_GUIDE.md` for implementation details and `docs/developer/LLM_PROVIDER_SPEC.md` for provider integration.

## Outputs and data layout

Typical output layout under `Documents/<Subject>/`:

- `pdfs/` — normalised PDF copies
- `markdown/` — converted Markdown and extracted images
- `document_reports/` — per-document CSV reports from LLM review passes

Additional data artefacts are produced under `data/` (state files, logs, and categoriser outputs). Notebooks under `notebooks/` and `docs/notebooks/` provide analysis and reporting examples.

## Configuration and environment variables

Key environment variables used by the LLM integrations:

- `GEMINI_API_KEY`
- `MISTRAL_API_KEY`
- `LLM_PRIMARY`, `LLM_FALLBACK`
- `LLM_CATEGORISER_BATCH_SIZE`, `LLM_CATEGORISER_MAX_RETRIES`

Refer to `docs/developer/LLM_PROVIDER_SPEC.md` for the full list and behavioural details.

## Known limitations

- **PDF conversion noise:** OCR artefacts (merged words, missing hyphens) can still surface; multi-pass filtering reduces, but does not eliminate, them.
- **Images are not fully checked:** Image-based text is only analysed if the converter extracts it into Markdown.
- **LLM runs require API keys:** Provider quotas and rate limits apply.

## Further documentation

- `docs/developer/ARCHITECTURE.md` — data flow, parsing rules, invariants
- `docs/developer/DEV_WORKFLOWS.md` — testing and debugging workflows
- `docs/methodology.md` — explanation of the proofreading approach
- `SCRIPTS.md` — helper scripts and batch processing utilities
