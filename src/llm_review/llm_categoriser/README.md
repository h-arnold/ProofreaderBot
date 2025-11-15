# LLM Categoriser

The purpose of the LLM categoriser module is to categorise language_tool issues created by `language_check.py`. It uses an LLM to assign each issue to a predefined category as defined in `models/enums.py`. The categories are:

-   **Parsing Error:** A "mechanical" error. e.g., `privacyfocused` (missing hyphen), `multi player` (should be one word or hyphenated), `fadein` (missing space).
-   **Spelling Error:** An incorrect spelling or the incorrect word version used out of context (e.g., "their" vs. "there", or a word not found in authoritative dictionaries like OED).
-   **Absolute Grammatical Error:** The grammar is definitively incorrect (e.g., "...learners should be **able review**..."). This includes non-UK spelling variants (e.g., `organize` vs. `organise`) or clear violations of a language's rules (e.g., incorrect gender/number agreement in French, as verified by sources).
-   **Possible/Ambiguous Grammatical Error:** Not necessarily incorrect, but potentially awkward, unclear, or non-standard (e.g., The tool's "consequences to" suggestion).
-   **Stylistic Preference:** The tool's suggestion is a stylistic choice (e.g., "in order to" vs. "to"), but the original text is not incorrect.
-   **False Positive:** The tool is wrong; the text is correct. This is often due to specialist terminology (`tweening`), proper names, complex sentences the tool misunderstands, or correct foreign-language words the tool misidentifies.

## Workflow

It begins by loading the issues from `Documents/language-check-report.csv` created by `language_check.py`. 

It then works, one document at a time (as identified by the `Filename` field) sending the issues to the LLM for categorisation. To manage LLM context size, it submits a configurable (via env vars) number of issues at time (default 10). For those issues, it will use the `report_utls.py` module to create a markdown table of the issue batch. It will use `page_utils.py` to extract the required pages from the original document for each issue. It will format the issues such that the each issue is provided with its matching page from the original document for context. 

It will use `prompt/render_prompt.py` to create the system and user prompts for the LLM. The prompt file templates are in `prompt/promptFiles` and they use pystache to render the prompts.

These will be sent to `llm/provider.py` which contains the LLM wrapper classes. There will be the option to submit these to the chat or batch endpoints. The default is to use the chat endpoint. 

It will then parse the LLM response and create or use a new folder in the `Documents/{subject} folder called {document_reports} which will open or create a new json file with the name of the document being processed. It will create a top-level key using the filename, and then add the returned json response as the values beneath.

Various processes will need to be created to handle the asyncronous nature of batch api requests.