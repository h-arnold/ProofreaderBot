# Language Check Configuration

The `language_check.py` tool checks Markdown documents for spelling and grammar issues using LanguageTool. It includes built-in filtering to reduce noise from common false positives.

## Default Filtering

### Disabled Rules

By default, the following LanguageTool rules are **disabled** to reduce noise:
- `WHITESPACE_RULE` - repeated whitespace
- `CONSECUTIVE_SPACES` - consecutive spaces
- `SENTENCE_WHITESPACE` - whitespace between sentences

### Ignored Words

The following words are **ignored** in spell-checking (case-insensitive):
- `wjec` - Welsh Joint Education Committee
- `cbac` - WJEC in Welsh (Cyd-bwyllgor Addysg Cymru)
- `fitzalan` - Fitzalan High School
- `llanwern` - Llanwern High School
- `gcse` - General Certificate of Secondary Education
- `tkinter` - Python GUI library

## Command-Line Options

### Adding Custom Ignored Words

```bash
# Add additional words to ignore
uv run python language_check.py --ignore-word "myword" --ignore-word "anotherword"

# Ignore only custom words (no defaults)
uv run python language_check.py --no-default-words --ignore-word "myword"
```

### Disabling Additional Rules

```bash
# Disable additional rules
uv run python language_check.py --disable-rule "MORFOLOGIK_RULE_EN_GB" --disable-rule "OXFORD_SPELLING_Z_NOT_S"

# Disable only custom rules (no defaults)
uv run python language_check.py --no-default-rules --disable-rule "MY_RULE"
```

### Finding Rule IDs

To find the rule ID for an issue you want to disable:
1. Run the language check and examine the report
2. Look in the "Rule" column of the Markdown table or the CSV file
3. Use the rule ID with the `--disable-rule` option

## Examples

### Check with defaults
```bash
uv run python language_check.py --root Documents --subject Computer-Science
```

### Check ignoring additional words
```bash
uv run python language_check.py --root Documents \
  --ignore-word "python" \
  --ignore-word "ide"
```

### Check with custom rules disabled
```bash
uv run python language_check.py --root Documents \
  --disable-rule "OXFORD_SPELLING_Z_NOT_S" \
  --disable-rule "HYPHEN_TO_EN"
```

### Check with no default filters
```bash
# Show all issues (no filtering)
uv run python language_check.py --root Documents \
  --no-default-rules \
  --no-default-words
```

## Modifying Defaults

To permanently change the default ignored words or disabled rules, edit `language_check.py`:

```python
# Near the top of the file
DEFAULT_DISABLED_RULES = {
    "WHITESPACE_RULE",
    "CONSECUTIVE_SPACES",
    "SENTENCE_WHITESPACE",
    # Add your rules here
}

DEFAULT_IGNORED_WORDS = {
    "wjec",
    "cbac",
    "fitzalan",
    # Add your words here
}
```

## Output

The tool generates two reports:
- **Markdown report** (`language-check-report.md`) - Human-readable table format
- **CSV report** (`language-check-report.csv`) - Machine-readable for filtering/analysis

Both reports include:
- Subject and filename
- Line and column numbers
- Rule ID and issue type
- Error message and suggestions
- Context showing the error
