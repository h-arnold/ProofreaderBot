# Data Notes

Current inputs used by the analysis notebook:
- `document_stats.csv` and `document_stats-files.csv` (summary and per-file stats)
- `Documents/language-check-report.csv` (issues from the language check pass)
- Pending: `notebooks/cleansed_data/language_check_categorised.csv` (categorised issues). The notebook will skip categorised analyses until this file is present.

When running locally:
- Place the categorised dataset at `notebooks/cleansed_data/language_check_categorised.csv`.
- Use `DOCS_LIGHT=1` to keep execution fast when the categorised file is missing.

CI will execute notebooks with `DOCS_LIGHT=1` and publish the rendered outputs to GitHub Pages on `master` pushes.
