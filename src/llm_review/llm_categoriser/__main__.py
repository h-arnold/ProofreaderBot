"""Main entry point for running the LLM categoriser as a module.

Usage:
    python -m src.llm_review.llm_categoriser [options]
"""

from __future__ import annotations

import sys

from .cli import main

if __name__ == "__main__":
    sys.exit(main())
