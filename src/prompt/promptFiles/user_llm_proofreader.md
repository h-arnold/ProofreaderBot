## Issue Batch

{{#issue_pages}}
### Page {{page_number}}
| issue_id | issue | highlighted_context |
| --- | --- | --- |
{{#issues}}
| {{issue_id}} | {{issue}} | {{highlighted_context}} |
{{/issues}}

Page context:
```markdown
{{{page_content}}}
```

---
{{/issue_pages}}

{{^issue_pages}}
{{{issue_table}}}
{{/issue_pages}}

---

---

**REMEMBER**: Use the error descriptions provided to categorise each issue accurately. You are assessing a piece of formal writing where the highest spelling and grammatical standards are expected.

Always categorise hyphenation errors as parsing errors. This is a common issue with the PDF to markdown converter.
