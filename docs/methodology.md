# WJEC Copyediting Results Analysis

## Overview

This notebook analyses the results from the various automated copyediting tools applied to the entire corpus of WJEC 'Made for Wales' GCSE documents. These were scraped directly from the WJEC website on November 8th 2025. I pushed them to GitHub at this time to ensure that there is an immutable record of the exact documents used for this analysis.

## Methodology

### Data Collection

1. **Scraping**: The documents were scraped from the WJEC website using a custom Python script that navigated to the relevant pages and downloaded the PDF files.
2. **Conversion**: The PDFs were converted to markdown using [Marker](https://github.com/datalab-to/marker), aided by `Gemini-2.5-Flash-Lite` to enchance text extraction quality. I also tried Docling and PDF2Markdown but marker produced the best results.

### Copyediting Process

Once processed, the proofreading tools were applied to markdown in passes, with each pass building on the previous one.

#### 1. Automated Proofreading Tools: Language Tool Spelling and Grammar Checker

This tool was used to prove that the WJEC had not even bothered to run a basic spelling and grammar check on their documents. It is a free and open-source spelling a grammar checker.

Unsurprisingly for educational documents, there were many specialist terms (over 2000) which needed to be added to an [ignore list](../src/language_check/language_check_config.py). After trying a few approaches, I ended up creating [this script](../script/manage_language_ignore.py) with this [ChatGPT4.1 custom chatmode](../.github/chatmodes/false_positive-iding.md.chatmode.md) to work through the results and generate a suitable ignore list. My role was simply to yay or nay the ignorelist suggestions to prevent false negatives creeping in. 

After a few passes to refine the ignore list, I was left with a final set of results. 

#### 2. LLM Based Phases

Despite the large ignore list for spellings and grammatical issues, there were still a significant number of false positives, particularly in relation to OCR conversion issues and in areas where in context, they were correct. The lack of context also meant that LanguageTool would miss other issues such as mispelled words in context, for example 'leaners' over learners. 

To address these issues, I created two additional LLM powered passes to build on the Language Tool results. Both passes use the same error categories to help classify all issues found. The error types identified across all passes are:

##### Error Categories

- **PARSING_ERROR**: Errors caused by the conversion from PDF to scanned text. These are typically garbled text that emerged when the PDF was converted to a readable format.
  - *What this means:* Missing or jumbled letters that make words look odd, like `Oueen` instead of `Queen`, or words fused together. These errors are a result of imperfect digital conversion, not actual mistakes in the original document.

- **SPELLING_ERROR**: Words that are spelled incorrectly or don't match British English conventions (since these are UK exam documents).
  - *What this means:* Typos or non-standard spellings, such as `definately` instead of `definitely`, or `Malcom` instead of `Malcolm`. These are genuine spelling mistakes.

- **ABSOLUTE_GRAMMATICAL_ERROR**: Clear breaks in sentence structure and grammar rules that are wrong in any context.
  - *What this means:* Missing words, incorrect word order, or wrong verb forms that make a sentence confusing or incorrect. For example, `collective highly qualified authors` (missing a verb), or `therefore, That...` (incorrect capitalisation mid-sentence).

- **CONSISTENCY_ERROR**: The text is correct on its own, but contradicts how the same thing is written elsewhere in the documents.
  - *What this means:* The document uses the same term or phrase in two different ways—like calling something both "war communism" and "war Communism" in different places. It could also mean using a wordy phrase like "due to the fact that" when "because" is used elsewhere.

- **AMBIGUOUS_PHRASING**: The sentence is technically correct, but the meaning is unclear or could be misunderstood.
  - *What this means:* Confusing sentence structure that makes it hard to understand who or what the sentence is about. For example: "Faced with the potential of radical elements, the demands were met..." could imply that the demands were facing the elements, rather than the government.

- **STYLISTIC_PREFERENCE**: Suggestions that the phrasing could be improved for clarity, professionalism, or tone, even though it's not technically wrong.
  - *What this means:* The text works but could be better. This only applies when the current wording genuinely makes the text harder to understand or sounds awkward. Minor preference changes (like "how we assess" vs. "assessment methodology") do not count.

- **FACTUAL_INACCURACY**: Statements or terminology that are objectively false or incorrect.
  - *What this means:* A factually wrong claim or misnamed term. For example, referring to Lenin's "April Theses" as the "April Thesis" (wrong name).

- **FALSE_POSITIVE**: Issues flagged by the tools that are not actually errors and require no correction.
  - *What this means:* The tools mistakenly flagged something as wrong when it's actually correct. This includes technical terminology, proper nouns, valid UK English conventions, or structural elements (like header echoes or table formatting) that don't need fixing.

##### Phase 1: LLM Assisted Language Tool Result Categorisation

To filter out the many false positives from Language Tool, and to make the categorisation process more efficient, I used Gemini-2.5-Flash to work through the Language Tool results and categorise them according to the categories above. Working in batches of 10 issues at a time, Gemini was supplied with the issue results from Language Tool, along with the matching page of text from the document to provide context. It would then cateogrise each issue as either:

 - False Positive
 - Paring Error
 - Spelling Error
 - Absolute Grammatical Error
 - Stylistic Preference

##### Phase 2: Full Document LLM Proofreading Pass

Language Tool is excellent at picking up word-level errors but struggles with sentence and paragraph level issues. LLMs, on the other hand, are not good at spotting word-level errors but excel at understanding context and sentence structure.

To get the best of both worlds, I've combined categorised output with Language Tool with a full document LLM proofreading pass.

In this phase, the entire document is processed by Gemini-2.5-Flash, 3 pages at a time, as I found that adding any more pages resulted in the LLM missing details. The LLM was provided with any existing issues found by Language Tool (after filtering out parsing errors and false positives) for the pages it was proof reading. It was prompted to search for the following error categories:

    - Spelling Errors
    - Absolute Grammatical Errors
    - Consistency Errors
    - Ambiguous Phrasing
    - Stylistic Preferences
    - Factual Inaccuracies

##### Future Phases

I had planned to create additional phases to do whole-document and whole-subject consistency checking. However, due to 10,000s of errors already found, I decided that I have more than enough evidence to demonstrate that standards at WJEC are criminally low.

#### 3. Manual Data Cleansing

Despite comprehensive instructions of what to ignore, especially in the final LLM Proofreading phase, there were still some false positives that crept in. Having looked at the data in Google Sheet, I identified some key phrases in the 'reasoning` column that were indicative of false positives such as:

- OCR
- missing space
- typographical error 
- backtick
- hyphenated without a space
- GCSF (these were all OCR conversion errors)
- space is missing

I added an extra column in the [LLM Proofreader Report](./cleansed_data/llm_proofreader_cleansed_data.csv) called 'Likely False Positive' and used a formula to flag any rows where the reasoning column contained any of these phrases.