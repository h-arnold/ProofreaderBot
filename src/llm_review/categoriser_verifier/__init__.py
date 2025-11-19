"""Categoriser verifier for LLM-categorised language tool issues.

This package orchestrates a verification pass over the output from llm_categoriser.
It takes the aggregated categorised report CSV as input and produces a verified
report CSV as output.

Main entry point:
    python -m src.llm_review.categoriser_verifier

Key differences from llm_categoriser:
    - Input: Documents/llm_categorised-language-check-report.csv
    - Output: Documents/verified-llm-categorised-language-check-report.csv
    - Uses system_categoriser_verifier prompt instead of system_language_tool_categoriser
    - Reuses user_language_tool_categoriser.md prompt
    - No per-document CSV outputs (single aggregated report)

Key modules:
    - prompt_factory: Render prompts with context (system_categoriser_verifier + user)
    - runner: Orchestrate workflow with retries
    - persistence: Write aggregated CSV output
    - config: Configuration dataclass
    - cli: Command-line interface
"""

from __future__ import annotations
