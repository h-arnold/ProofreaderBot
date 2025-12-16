"""Shared utilities for notebooks that explore the cleansed document stats data."""

from __future__ import annotations

import sys
from importlib import import_module
from pathlib import Path
from typing import Any, Sequence


def require_modules(names: Sequence[str], group: str = "docs") -> dict[str, Any]:
    modules: dict[str, Any] = {}
    missing: list[str] = []
    last_exc: ModuleNotFoundError | None = None
    for fullname in names:
        try:
            modules[fullname] = import_module(fullname)
        except ModuleNotFoundError as exc:
            missing.append(fullname)
            last_exc = exc
    if missing:
        raise ModuleNotFoundError(
            f"Missing modules {missing}. Install them with `uv sync --only-group {group}` or `uv add {' '.join(missing)}`."
        ) from last_exc
    return modules


_MODULES = require_modules(["pandas", "plotly", "plotly.express"])
pd: Any = _MODULES["pandas"]
plotly: Any = _MODULES["plotly"]
px: Any = _MODULES["plotly.express"]


def find_repo_root(start: Path) -> Path:
    current = start.resolve()
    for _ in range(8):
        if (current / "pyproject.toml").exists():
            return current
        if current.parent == current:
            break
        current = current.parent
    raise FileNotFoundError("Could not locate repo root (pyproject.toml)")


REPO_ROOT = find_repo_root(Path.cwd())
DATA_DIR = REPO_ROOT / "notebooks" / "cleansed_data"
DATA_FILES = DATA_DIR / "document-stats-files.csv"
DATA_ISSUES = DATA_DIR / "normalised-language-reports.csv"


def load_document_stats() -> tuple[Any, Any]:
    missing_files = [path for path in (DATA_ISSUES, DATA_FILES) if not path.exists()]
    if missing_files:
        names = ", ".join(str(path) for path in missing_files)
        raise FileNotFoundError(f"Required cleansed data files are missing: {names}.")
    issues = pd.read_csv(DATA_ISSUES)
    files = pd.read_csv(DATA_FILES)
    return issues, files


def print_environment_info() -> None:
    print("Python:", sys.version.splitlines()[0])
    print("Pandas:", pd.__version__)
    print("Plotly:", plotly.__version__)
    print("Repo root:", REPO_ROOT)
    print("Data dir:", DATA_DIR)


print_environment_info()
issues, files = load_document_stats()
print("Loaded issues:", issues.shape, "files:", files.shape)
