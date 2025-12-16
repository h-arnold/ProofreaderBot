# This script exists because it's quicker and easier just to normalise and process the outputs from the different checking phases than it is to go back and de-slopify the code and get everything consistent.
# Hopefully it won't be necessary to use this code again in the future. If it is, Godspeed!

"""Normalise and merge the post-proofreading CSV exports."""

from __future__ import annotations

import argparse
import csv
from pathlib import Path
from typing import Iterable, MutableMapping

CATEGORY_MAP: dict[str, str] = {
    "ABSOLUTE_GRAMMATICAL_ERROR": "Grammar",
    "GRAMMAR": "Grammar",
    "SPELLING_ERROR": "Spelling",
    "SPELLING": "Spelling",
    "CONSISTENCY_ERROR": "Consistency",
    "CONSISTENCY": "Consistency",
    "AMBIGUOUS_PHRASING": "Ambiguous Phrasing",
    "AMBIGUOUS_PHRASE": "Ambiguous Phrasing",
    "FACTUAL_INACCURACY": "Factual",
    "FACTUAL": "Factual",
    "STYLISTIC_PREFERENCE": "Stylistic",
    "STYLISTIC": "Stylistic",
    "FALSE_POSITIVE": "False Positive",
    "PARSING_ERROR": "Parsing Error",
    "PARSING": "Parsing Error",
}

OUTPUT_COLUMNS = [
    "Subject",
    "File Name",
    "Document Name",
    "Issue ID",
    "Page Number",
    "Issue",
    "Context",
    "Pass Code",
    "Error Category",
    "Confidence Score",
    "Reasoning",
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Normalise and combine the LanguageTool and LLM proofreader CSV exports."
    )
    parser.add_argument(
        "--language-report",
        type=Path,
        default=Path("notebooks/cleansed_data/verfied-language-check-reports.csv"),
        help="LanguageTool derived CSV export",
    )
    parser.add_argument(
        "--proofreader-report",
        type=Path,
        default=Path("notebooks/cleansed_data/llm_proofreader_cleansed_data.csv"),
        help="LLM proofreader CSV export",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("notebooks/cleansed_data/normalized-language-reports.csv"),
        help="Path for the merged CSV",
    )
    return parser.parse_args()


def normalise_string(raw: str | None) -> str:
    return (raw or "").strip()


def normalise_subject(value: str | None) -> str:
    cleaned = (value or "").replace("-", " ")
    cleaned = cleaned.replace("_", " ")
    return " ".join(cleaned.split())


def normalise_document_name(filename: str | None) -> str:
    if not filename:
        return ""
    suffix = filename
    if "---" in filename:
        suffix = filename.split("---", 1)[1]
    stem = Path(suffix).stem
    cleaned = stem.replace("-", " ").replace("_", " ")
    words = [word.capitalize() for word in cleaned.split() if word]
    return " ".join(words)


def normalise_error_category(raw: str | None) -> str:
    if not raw:
        return ""
    candidate = raw.split(".", 1)[-1].strip()
    key = candidate.upper().replace(" ", "_")
    mapped = CATEGORY_MAP.get(key)
    if mapped:
        return mapped
    return candidate.title()


def normalise_pass_code(raw: str | None) -> str:
    clean = normalise_string(raw)
    if "." in clean:
        clean = clean.split(".", 1)[-1]
    return clean


def normalise_row(row: MutableMapping[str, str]) -> dict[str, str]:
    lower_row = {key.lower(): value for key, value in row.items()}
    subject = normalise_subject(lower_row.get("subject"))
    filename = normalise_string(lower_row.get("filename"))
    document_name = normalise_document_name(filename)

    context = lower_row.get("context") or lower_row.get("highlighted_context", "")

    result: dict[str, str] = {
        "Subject": subject,
        "File Name": filename,
        "Document Name": document_name,
        "Issue ID": normalise_string(lower_row.get("issue_id"))
        or normalise_string(lower_row.get("issue id")),
        "Page Number": normalise_string(lower_row.get("page_number"))
        or normalise_string(lower_row.get("page number")),
        "Issue": normalise_string(lower_row.get("issue")),
        "Context": normalise_string(context),
        "Pass Code": normalise_pass_code(
            lower_row.get("pass_code") or lower_row.get("pass code")
        ),
        "Error Category": normalise_error_category(
            normalise_string(lower_row.get("error_category"))
            or normalise_string(lower_row.get("error category"))
        ),
        "Confidence Score": normalise_string(lower_row.get("confidence_score"))
        or normalise_string(lower_row.get("confidence score")),
        "Reasoning": normalise_string(lower_row.get("reasoning")),
    }

    likely_fp = normalise_string(lower_row.get("likely false positive"))
    if likely_fp and likely_fp.strip().upper() == "TRUE":
        # Force category to False Positive when the flag is set
        result["Error Category"] = "False Positive"

    return result


def iter_rows(path: Path) -> Iterable[dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            yield normalise_row(row)


def main() -> None:
    args = parse_args()
    args.output.parent.mkdir(parents=True, exist_ok=True)

    with args.output.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=OUTPUT_COLUMNS)
        writer.writeheader()
        total = 0
        for source in (args.language_report, args.proofreader_report):
            for normalized in iter_rows(source):
                writer.writerow(normalized)
                total += 1
    print(f"Wrote {total} rows to {args.output}")


if __name__ == "__main__":
    main()
