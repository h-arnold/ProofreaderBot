# Methodology

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

To address these issues, I created two additional LLM powered passes to build on the Language Tool results. Both passes use the same issue categories to help classify all issues found. 

[Read more about the issue categories here.](./issue_categories.md)


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

Finally, all of this data is normalised using a quick Python script to ensure that all columns are consistent and correctly typed. This is quicker than de-slopifying the actual code to ensure that outputs are consistent across all modules.