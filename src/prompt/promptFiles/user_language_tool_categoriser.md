<!-- Document header (header, inputs, task) is defined in the system prompt
	to keep static role instructions separate from per-batch content. -->

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

