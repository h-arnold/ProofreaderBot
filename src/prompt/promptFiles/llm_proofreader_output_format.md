## Output Format

Return a **single top-level JSON array** (no surrounding object, no page keys) and nothing else. Do not include backticks, commentary, or any text before or after the JSON. Each array element represents one issue from the table.

For each issue, return either a minimal categorisation object (see "Minimal format" below) or a full issue object (see "Full format" below). In both cases, return a **single top-level JSON array** containing one object per issue.

- `issue_id`: integer — the issue identifier from the input CSV (auto-increment per-document)
- `issue`: The specific word or short phrase containing the error.
- `highlighted_context`: The sentence containing the error (plus the preceding sentence if necessary for clarity) with the error highlighted using double asterisks `**` before and after the error. **Maximum 2 sentences.**
- `error_category`: one of the enum values listed in "Error Categories" above (e.g., `SPELLING_ERROR`)
- `confidence_score`: integer 0–100 (if you prefer to provide 0–1 floats, the runner will convert them)
- `reasoning`: single-sentence justification

Note: These fields map directly to the `LanguageIssue` model. When you return the minimal format (with `issue_id`), the runner will merge the LLM fields into the original `LanguageIssue` object. When the full format is returned, the runner will validate it with `LanguageIssue.from_llm_response()` and construct a full `LanguageIssue` instance.

Full format (optional):
If your provider cannot reference the original issues by `issue_id`, return a full record using these fields. The runner will validate it using `LanguageIssue.from_llm_response()`.
```json
[
  {
    "issue_id": 0,
    "issue": "loose",
    "highlighted_context": "The students **loose** several marks for poor grammar.",
    "error_category": "SPELLING_ERROR",
    "confidence_score": 95,
    "reasoning": "Common misspelling of 'lose' in this context."
  },
  {
    "issue_id": 1,
    "issue": "well-run",
    "highlighted_context": "This was a **well-run** event that concluded smoothly.",
    "error_category": "PARSING_ERROR",
    "confidence_score": 88,
    "reasoning": "Compound adjective requires hyphenation in UK English when used before a noun."
  }
]
```


Each error object **must** include only the fields described above.

IMPORTANT: Always return a JSON array even for a single issue. For example, the array may be the minimal form:

Or the full form (including `issue` and `highlighted_context`):

```json
[
  {
    "issue_id": 0,
    "issue": "loose",
    "highlighted_context": "The students **loose** several marks for poor grammar.",
    "error_category": "SPELLING_ERROR",
    "confidence_score": 95,
    "reasoning": "Common misspelling of 'lose' in this context."
  }
]
```

Do not return the single object without wrapping it in an array. Also ensure every string uses double-quotes and there are no trailing commas.

---