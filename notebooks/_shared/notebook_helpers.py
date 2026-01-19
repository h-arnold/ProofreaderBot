"""Notebook helper utilities for sampling and displaying issues.

Place this file in `notebooks/_shared/` and run it from notebooks with:

%run _shared/notebook_helpers.py
"""

from typing import Iterable, Optional

import pandas as pd
from IPython.display import Markdown, display


def normalize_subjects(df: pd.DataFrame) -> pd.DataFrame:
    """Return a copy of `df` with `Subject` values normalized (hyphens -> spaces)."""
    df = df.copy()
    if "Subject" in df.columns:
        df["Subject"] = df["Subject"].astype(str).str.replace("-", " ")
    return df


def display_issues_table(
    df: pd.DataFrame, cols: Optional[Iterable[str]] = None, max_rows: int = 50
) -> None:
    """Display a DataFrame as a Markdown table (head only).

    This keeps notebook outputs compact and nicely formatted for MkDocs.
    """
    if cols is None:
        cols = [
            "Subject",
            "Document Name",
            "Page Number",
            "Context",
            "Issue",
            "Confidence Score",
            "Reasoning",
        ]
    cols = [c for c in cols if c in df.columns]
    if df.empty:
        display(Markdown("**No rows to display.**"))
        return
    display(Markdown(df.loc[:, cols].head(max_rows).to_markdown(index=False)))


def sample_factual_issues(
    issues_df: pd.DataFrame, n: int = 20, random_state: int = 42
) -> pd.DataFrame:
    """Return a random sample of up to `n` factual issues from the whole corpus."""
    factual = issues_df[issues_df["Issue Category"].str.casefold() == "factual"].copy()
    factual = normalize_subjects(factual)
    if factual.empty:
        return factual
    return factual.sample(n=min(n, len(factual)), random_state=random_state)


def sample_factual_by_subject(
    issues_df: pd.DataFrame,
    per_subject: int = 10,
    subjects: Optional[Iterable[str]] = None,
    random_state: int = 42,
) -> pd.DataFrame:
    """Return up to `per_subject` factual issues for each subject.

    - If `subjects` is None, the function uses the subjects that appear in the factual subset.
    - The returned DataFrame contains an extra column `Sampled Subject` to indicate which subject the sample belongs to.
    """
    df = normalize_subjects(issues_df)
    factual = df[df["Issue Category"].str.casefold() == "factual"]
    if factual.empty:
        return pd.DataFrame(columns=factual.columns.tolist() + ["Sampled Subject"])

    if subjects is None:
        subjects = sorted(factual["Subject"].dropna().unique())

    parts = []
    for subj in subjects:
        s = factual[factual["Subject"] == subj]
        if s.empty:
            continue
        sampled = s.sample(n=min(per_subject, len(s)), random_state=random_state)
        sampled = sampled.copy()
        sampled["Sampled Subject"] = subj
        parts.append(sampled)

    if not parts:
        return pd.DataFrame(columns=factual.columns.tolist() + ["Sampled Subject"])
    return pd.concat(parts, ignore_index=True)


__all__ = [
    "normalize_subjects",
    "display_issues_table",
    "sample_factual_issues",
    "sample_factual_by_subject",
]
