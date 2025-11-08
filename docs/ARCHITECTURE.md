# Architecture and API Contracts (MUST CONSULT BEFORE CODE CHANGES)

This document defines how the scraper works, the public contracts you must preserve, and where to make changes safely.

## Overview

The tool downloads GCSE PDF documents from WJEC “Made for Wales” qualification pages. It can be used via:
- CLI: `main.py`
- Library API: `wjec_scraper.py`

Python >= 3.12. Dependencies are managed with uv (see `docs/UV_GUIDE.md`).

## Data flow

1. Subject selection
   - Subjects are defined by `QUALIFICATION_URLS: dict[str, str]` (name → landing URL).
   - The CLI matches subject names case-insensitively.

2. HTML acquisition
   - `fetch_html(url: str) -> str`
   - Uses `requests` to GET (or sometimes POST) pages.
   - For some subjects, an additional site-specific key-documents endpoint is probed; absence or failure is non-fatal.

3. Link discovery (two strategies combined)
   - `iter_pdf_links(html: str) -> Iterable[tuple[url, title]]`
     - Anchors with href ending in `.pdf`.
   - `iter_pdf_from_react_props(html: str) -> Iterable[tuple[url, title]]`
     - Parses embedded React props JSON inside `textarea.react-component--props`.
     - Extracts `listItems` entries with `Link` (URL) and `Name` (title).

4. Coalescing and title choice
   - `collect_pdf_links(html_or_pages: ...) -> dict[url, best_title]`
   - URLs are de-duplicated; the “best” title is chosen by preferring the longest non-empty title per URL.

5. Filenames and directories
   - `subject_directory_name(subject: str) -> str`
     - Normalises to filesystem-safe dir name (non-alphanumerics → `-`).
   - `sanitise_filename(title: str, url: str, existing: set[str]) -> str`
     - Lowercase, hyphenated, suffix `-N` added if needed to avoid collisions.

6. Downloading
   - `download_file(url: str, dest: Path) -> None`
     - Uses `requests` to download bytes; partial files are removed on error.
   - `download_subject_pdfs(subject: str, output_dir: Path, reporter: Callable[[str, Path, str], None] | None = None) -> None`
     - Drives the end-to-end process for a subject.
     - Calls `reporter(label, destination, url)` for progress if provided.

## Public API (contracts)

Keep function names, parameter orders, and behaviors stable unless you update all call sites and the CLI accordingly.

- `fetch_html(url) -> str`
  - Must raise for non-recoverable HTTP errors; may return empty string only on explicitly handled non-fatal conditions.

- `iter_pdf_links(html) -> Iterable[(url, title)]`
  - Must ignore non-PDF links; return absolute URLs when possible.

- `iter_pdf_from_react_props(html) -> Iterable[(url, title)]`
  - Must be resilient to missing/invalid JSON; return an empty iterator on failure.

- `collect_pdf_links(...) -> dict[url, title]`
  - Must deduplicate URLs and choose the longest non-empty title per URL.

- `subject_directory_name(subject) -> str`
  - Must replace non-alphanumeric with `-`, coalesce repeats, and trim leading/trailing `-`.

- `sanitise_filename(title, url, existing) -> str`
  - Must be lowercase, hyphenated; must avoid collisions by appending `-N` where N ≥ 2.

- `download_subject_pdfs(subject, output_dir, reporter=None) -> None`
  - Must call `reporter(label, destination, url)` when provided.
  - Must not crash on individual network/IO errors; continue with other files.

## Parsing rules and edge cases

- Key-documents endpoint: Some subjects expose PDFs only via this endpoint; the scraper should attempt to fetch it and proceed if unavailable.
- React props: Props are found in `textarea.react-component--props`; structure contains `listItems` with `Name` and `Link`.
- Titles: Prefer more descriptive (longer) titles when multiple are available for the same URL.
- Duplicates: Same URL appears once; filenames still must be unique on disk (use `sanitise_filename`).

## Change guidelines (must follow)

- Subjects
  - Edit `QUALIFICATION_URLS` in `wjec_scraper.py` to add/remove subjects. Keep user-facing names stable; CLI matches case-insensitively.

- Filenames and directories
  - Do not change normalization logic casually. If you must, update both `sanitise_filename` and `subject_directory_name` together and verify no regressions in already-downloaded structures.

- Progress reporting
  - Keep the `reporter(label, destination, url)` hook; the CLI depends on it for user feedback.

- Error handling
  - Log and continue on network/IO errors; ensure partial files are cleaned up on failure.

- Performance
  - Current implementation is synchronous and acceptable for the expected dataset size. If adding concurrency, ensure deterministic filenames and avoid race conditions when writing files.

## When to update this document

- You add/remove public functions in `wjec_scraper.py`.
- You change filename or directory normalization.
- You modify how subjects are configured or matched.
- You change link-discovery strategies or title selection rules.
