"""Main entry point for running the categoriser verifier as a module.

Usage:
    python -m src.llm_review.categoriser_verifier [options]
"""

from __future__ import annotations

import sys

from .cli import main

if __name__ == "__main__":
    sys.exit(main())
