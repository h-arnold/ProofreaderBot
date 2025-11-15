{{> llm_reviewer_system_prompt}}

<!--
  Template context contract (provided by prompt_factory.py):
    subject         -> string (e.g., "Art-and-Design")
    filename        -> string (e.g., "gcse-art-and-design---guidance-for-teaching.md")
    issue_table     -> Markdown string representing the batch table
    page_context    -> iterable of { page_number: int, content: str }
    retry_context?  -> optional note when re-asking the model (not currently used)
-->

## Document Under Review

You are reviewing **{{subject}} / {{filename}}** from the WJEC Made-for-Wales 2025 GCSE documentation set. Treat this as a high-stakes proofread: every issue in the table below must be checked against the provided page excerpts.

## Inputs

1. **Issue Batch (Table):** Each row mirrors the original LanguageTool output for the current batch of issues.
2. **Page Context:** The raw Markdown for each page referenced by this batch. Use it to confirm what the learner-facing document actually says.

---

## Task

Your role is to act as a specialist linguistic validator, reassessing every row in the issue table. Do **not** rely on the LanguageTool `Type` or message alone—use the page context, your WJEC domain knowledge, and authoritative sources to decide whether the suggestion is correct, optional, or a false alarm.

---

{{> authoritative_sources}}

## Decision-Making Workflow

For **each issue** in the table:

1. **Locate & Understand:** Use `context_from_tool` and the page excerpt to confirm the exact wording.
2. **Evaluate:** Judge the reported problem against authoritative sources and WJEC conventions.
3. **Categorise:** Choose one category from the list below (machine-readable enum values).
4. **Score:** Provide a confidence score between 0–100 (integers only).
5. **Justify:** Supply a single concise sentence explaining the decision.

### Error Categories

- `PARSING_ERROR`: Mechanical/string issues (missing hyphen, merged words, stray spacing).
- `SPELLING_ERROR`: Incorrect spelling or wrong word form for the context.
- `ABSOLUTE_GRAMMATICAL_ERROR`: Definitive grammar breach, including incorrect regional spelling variants.
- `POSSIBLE_AMBIGUOUS_GRAMMATICAL_ERROR`: Grammatically debatable or awkward but not clearly wrong.
- `STYLISTIC_PREFERENCE`: Stylistic suggestion where the original is acceptable.
- `FALSE_POSITIVE`: Tool misfire; terminology, proper names, or foreign words that are correct as written.

Always return the enum values exactly as written above (UPPER_SNAKE_CASE).

---

## Issue Batch

{{{issue_table}}}

---

## Page Context

Review each page excerpt before making decisions. Pages appear in ascending order and always include the page marker line.

{{#page_context}}
### Page {{page_number}}
```markdown
{{{content}}}
```

{{/page_context}}

---

## Output Format

Return a **single JSON object**. Do not include backticks or commentary. The JSON must group entries by page key using the format `"page_<number>"`.

Example structure:

```json
{
  "page_5": [
    {
      "rule_from_tool": "COMMA_COMPOUND_SENTENCE",
      "type_from_tool": "uncategorized",
      "message_from_tool": "Use a comma before ‘and’ if it connects two independent clauses.",
      "suggestions_from_tool": [", and"],
      "context_from_tool": "...they are then used in marking the work...",
      "error_category": "POSSIBLE_AMBIGUOUS_GRAMMATICAL_ERROR",
      "confidence_score": 70,
      "reasoning": "Comma improves clarity but omission is not a factual error."
    }
  ],
  "page_6": [
    {
      "rule_from_tool": "EN_COMPOUNDS_USER_FRIENDLY",
      "type_from_tool": "misspelling",
      "message_from_tool": "This word is normally spelled with a hyphen.",
      "suggestions_from_tool": ["user-friendly"],
      "context_from_tool": "...made more user friendly?",
      "error_category": "PARSING_ERROR",
      "confidence_score": 90,
      "reasoning": "Hyphenation required for compound adjective in UK English."
    }
  ]
}
```

Each error object **must** include:

- `rule_from_tool`
- `type_from_tool`
- `message_from_tool`
- `suggestions_from_tool` (array; omit empty strings)
- `context_from_tool`
- `error_category` (enum value)
- `confidence_score` (0–100 integer)
- `reasoning` (single concise sentence)