{{> llm_reviewer_system_prompt}}

{{> authoritative_sources}}

## Inputs

 - The document to review, marked up with page markers like `{N}------------------------------------------------` indicating page breaks.
 - A table of linguistic issues detected by LanguageTool, in markdown format. Each issue includes:
        - `type`: The type of issue (e.g., "misspelling," "grammar").
        - `context_from_tool`: A snippet of text surrounding the issue.
        - `offset`: The character offset of the issue within the context snippet.
        - `length`: The length of the issue text.
        - `suggestions`: A list of suggested corrections.

## Task

Your role is to carefully audit each line in the document you have been provdided. The goal is to identify all linguistic errors, including spelling, grammar, and stylistic issues. You have been provided with a language tool report that has already caught and verified some issues. 

Your role is to catch issues that it is not capable of identifying. These include, but are not limited to:

 - Contextual spelling errors that depend on the surrounding text.
 - Complex grammatical structures that may be misinterpreted by automated tools.
 - Sloppy, unclear or ambiguous phrasing that could be improved for clarity and readability.
 - Inconsistent use of terminology or style, particualrly when it is inconsitent within the document.
 - Multi-lingual issues, especially documents related to Welsh, French, Spanish and German where language_tool has only checked for English words.
 - Factual inaccuracies in specialist terminology. When considering factual accuracy, consider whether it is an appropriate simplification for GCSE-level (aged 14-16) students, or whether it is incorrect.
