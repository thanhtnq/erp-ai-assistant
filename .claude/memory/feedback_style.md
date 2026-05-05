---
name: Response Format & Style Rules
description: Confirmed rules for chatbot response formatting — what to avoid and what works
type: feedback
originSessionId: f63f54d9-5d34-44e5-9bb2-c7fa26764c3f
---
Rules confirmed through iterative screenshot review.

**Why:** User compared RAG and data_query responses side by side and wanted consistent style.

**How to apply:** When editing Round 3 prompt, ROLE.md, or any LLM instruction that controls output format.

## Data Query Response Format (confirmed working)
- 1–2 plain sentences for the result — no bold `**Label: value**` redundancy
- ALL monetary amounts: always append currency code (e.g. `66,197,143.79 SGD`) from `curr_short_forex`
- Markdown table only when multiple rows
- Blank line before closing question
- Exactly ONE friendly closing question (emoji OK) — NO bullet list of suggestions
- Closing rendered via `closing` SSE event → separate CSS block with border-top (same as RAG)

## What NOT to Do
- No numbered section headers (1. Opening 2. Data 3. Suggestions) — looks mechanical
- No "Here are some follow-up questions you might consider:" intro to bullets
- No 3-bullet suggestion lists in data_query responses
- No bold `**Total Sales Order Amount (2010): 66,197,143.79**` — redundant if stated in sentence
- No "Would you like to explore this data further?" — too generic

## RAG Path Closing (reference style)
Single friendly question at end, e.g.:
"Would you like me to explain any of these fields in more detail or help with posting? 😊"
Data query closing should match this tone exactly.
