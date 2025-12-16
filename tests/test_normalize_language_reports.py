import sys
from pathlib import Path

# Ensure repository root is on sys.path so test imports work when run in CI/local
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from scripts.normalize_language_reports import normalise_row


def make_row(**kwargs):
    # Provide some reasonable defaults and allow overrides
    base = {
        "subject": "Art-and-Design",
        "filename": "gcse-art-and-design---guidance-for-teaching.csv",
        "issue_id": "1",
        "page number": "10",
        "issue": "example",
        "error_category": "Grammar",
        "reasoning": "something",
        "confidence score": "80",
    }
    base.update(kwargs)
    return base


def test_overrides_error_category_when_likely_true():
    row = make_row(**{"likely false positive": "TRUE"})
    out = normalise_row(row)
    assert out["Error Category"] == "False Positive"
    # Ensure the internal flag is not exposed in the output
    assert "Likely False Positive" not in out


def test_does_not_override_when_not_true():
    row = make_row(**{"likely false positive": "false", "error_category": "Spelling"})
    out = normalise_row(row)
    assert out["Error Category"] == "Spelling"
    assert "Likely False Positive" not in out
