# Dev Workflows and Testing (MUST CONSULT BEFORE TESTING OR DEBUGGING)

This guide lists quick checks, debugging patterns, and testing conventions for the scraper.

## Quick Checks

- List subjects:
```bash
uv run python main.py --list-subjects
```
- Dry-run a subject without writing files:
```bash
uv run python main.py --subjects Geography --dry-run
```
- Try multiple subjects and custom output:
```bash
uv run python main.py --subjects "Art and Design" French -o ./wjec-pdfs
```

## Interactive Debugging

Launch a REPL with project deps:
```bash
uv run python
```
In REPL:
```python
from wjec_scraper import (
    fetch_html,
    collect_pdf_links,
    iter_pdf_links,
    iter_pdf_from_react_props,
    sanitise_filename,
    subject_directory_name,
)
html = fetch_html("https://example.com/subject")
links = list(iter_pdf_links(html))
react_links = list(iter_pdf_from_react_props(html))
filename = sanitise_filename("Sample PDF", "https://example.com/sample.pdf", set())
```

## Minimal Test Scaffold

We use pytest. Add it first if missing:
```bash
uv add --dev pytest
```
Example tests to start with (create `tests/test_filenames.py`):
```python
import re
from wjec_scraper import sanitise_filename, subject_directory_name

def test_subject_directory_name_basic():
    assert subject_directory_name("Cymraeg Language and Literature").startswith("Cymraeg-Language")


def test_sanitise_filename_uniqueness():
    existing = {"doc.pdf", "doc-2.pdf"}
    name = sanitise_filename("Doc", "http://x/doc.pdf", existing)
    assert re.match(r"doc-(\d+)\.pdf", name)
```
Run tests:
```bash
uv run pytest -q
```

## Logging and Failure Handling

- Network/IO errors should log a message and continue; partial files are removed on failure.
- Duplicate URLs are coalesced; duplicate filenames receive `-N` suffixes.

## PR Hygiene & Validation

- Keep changes small and aligned with contracts in `docs/ARCHITECTURE.md`.
- After any scraping or filename change:
  - Run a dry-run for a couple of subjects.
  - If tests exist, run `uv run pytest` and fix failures.

## When to Update This Document

- New debugging utilities or reporter hooks are added.
- We adopt a new testing pattern or directory structure.
