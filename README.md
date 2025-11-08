# WJEC Document Scraper

Command-line tool for downloading PDF documents exposed on the WJEC GCSE Made-for-Wales qualification pages. The scraping logic lives in `wjec_scraper.py` and can be reused programmatically, while `main.py` provides a friendly CLI.

## Requirements

- Python 3.12 or newer
- `requests`
- `beautifulsoup4`

Install the dependencies into a virtual environment with:

```bash
python -m venv .venv
source .venv/bin/activate
pip install .
```

## CLI Usage

List every subject that the scraper knows about:

```bash
python main.py --list-subjects
```

Download all configured subjects into the default `Documents/` folder:

```bash
python main.py
```

Download a subset of subjects into a custom directory:

```bash
python main.py --subjects "Art and Design" French --output ./wjec-pdfs
```

Preview what would be downloaded without touching the filesystem:

```bash
python main.py --subjects Geography --dry-run
```

All files are grouped by subject using a filesystem-safe folder name, and duplicate filenames are handled automatically by appending numeric suffixes where required.
