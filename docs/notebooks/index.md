# Notebooks

Rendered notebooks are published here for quick, read-only access. The source notebooks live under `notebooks/` and can be run locally for experimentation.

Local tips:
- Run `uv sync --group docs` to ensure notebook and MkDocs tooling are installed.
- Execute the data overview notebook locally with:
  - `uv run python -m jupyter nbconvert --to notebook --execute notebooks/data_overview.ipynb --output docs/notebooks/data_overview.ipynb`
- Or open it interactively in VS Code/Jupyter and save the executed copy into `docs/notebooks/` before running `uv run mkdocs serve`.

CI will execute the notebook with `DOCS_LIGHT=1`, write the executed copy to `docs/notebooks/data_overview.ipynb`, and publish the site on `master` pushes.
