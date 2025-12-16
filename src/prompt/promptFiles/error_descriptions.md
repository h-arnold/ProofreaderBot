### Error Categories

- `PARSING_ERROR`: Errors likely caused by the conversion from PDF to markdown.
    - **Examples:** missing hyphens, merged words, stray spacing, words with similar shape to the misspelling e.g. `Oueen` instead of `Queen`, `vntil` instead of `until` or `ves` instead of `yes`.
- `SPELLING_ERROR`: The token is not a valid word in the dictionary for the target dialect. For English, always use British English spelling and conventions.
    - **Examples:** `Malcom X` (should be Malcolm), `warravaged` (missing hyphen), `definately`.
- `ABSOLUTE_GRAMMATICAL_ERROR`: An objective breach of syntax rules - wrong in all contexts.
    - **Examples:** Missing prepositions (`collective highly qualified authors`), extra words (`quantity and of goods`), or capitalisation errors (`therefore, That...`).
- `STYLISTIC_PREFERENCE`: Stylistic suggestion where the original is awkward, confusing, or unprofessional.
    - **Restriction:** Do NOT use this for simple preference variations (e.g., changing "how we assess" to "assessment methodology"). Only flag if the current phrasing actively hinders comprehension or tone.
- - `FALSE_POSITIVE`: 
    1. The text is actually correct (tool misfire).
    2. The issue is a valid stylistic choice common in UK English.
    3. The issue is a structural artifact (Header Echo, Table Row) that does not require linguistic correction.
    4. Technical terminology, proper nouns, or code.

Always return the enum values exactly as written above (UPPER_SNAKE_CASE).

#### Notes on commas before conjunctions separating independent clauses

When LanguageTool suggests adding a comma before a conjunction (e.g., "and", "but", "or") that separates two independent clauses, note this as:

    - `ABSOLUTE_GRAMMATICAL_ERROR` if the absence of a comma creates ambiguity or misleads the reader.
    - `STYLISTIC_PREFERENCE` if adding a comma wouldn't impact clarity.
