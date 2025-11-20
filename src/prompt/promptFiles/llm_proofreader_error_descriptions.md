### Error Categories

- `SPELLING_ERROR`: The token is not a valid word in the dictionary for the target dialect (e.g., US vs UK English).
    - **Examples:** `definately`, `teh`, or using `colour` in a document explicitly defined as US English.
- `CONTEXTUAL_SPELLING`: Valid dictionary words used incorrectly (homophones, typos resulting in real words).
    - **Examples:** `their` vs `there`, `assess` vs `access`, `leaners` vs `learners`.
- `GRAMMATICAL_ERROR`: An objective breach of syntax rules. If the sentence structure is technically invalid, it belongs here.
    - **Includes:** Subject-verb agreement, incorrect verb tense, article misuse, prepositions used incorrectly, comma splices, and sentence fragments.
- `STYLISTIC_PREFERENCE`: The text is grammatically correct and the meaning is clear, but the phrasing is verbose, passive, awkward, or informal.
    - **Includes:** Passive voice suggestions, removing redundancy, improving flow, and optional punctuation changes (e.g., Oxford comma).
- `CONSISTENCY_ERROR`: The usage is valid in isolation but contradicts patterns established elsewhere in the text.
    - **Examples:** Mixing `web site` and `website`, alternating between Title Case and Sentence case in headers, or switching between `UK` and `U.K.`
- `AMBIGUOUS_PHRASING`: The text is grammatically correct, but the semantic meaning is unclear or open to multiple interpretations.
    - **Criteria:** Use this when a reader could reasonably interpret the sentence in two different ways.

Always return the enum values exactly as written above (UPPER_SNAKE_CASE).

#### Rules for Commas before Conjunctions (and, but, or)

Classify comma issues between independent clauses using the following hierarchy:

1.  **`GRAMMATICAL_ERROR`**: Use this if the text contains a **comma splice** (two independent clauses joined only by a comma without a conjunction) or a **run-on sentence** (two independent clauses joined with no punctuation).
2.  **`AMBIGUOUS_PHRASING`**: Use this if the absence (or presence) of the comma causes the subject of the second clause to be misidentified.
3.  **`STYLISTIC_PREFERENCE`**: Use this for all other optional comma suggestions intended to change the pacing or "flow" of the sentence.