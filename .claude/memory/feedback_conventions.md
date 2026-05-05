---
name: Project Conventions & Feedback
description: Behavioral rules specific to this project — what to do automatically when triggered
type: feedback
---

## "cập nhật CLAUDE.md" trigger

When user says "cập nhật CLAUDE.md", always update BOTH:
1. `CLAUDE.md` — relevant section
2. `.claude/memory/` — create or update relevant memory file(s)

**Why:** User wants a single command that keeps all documentation in sync.
**How to apply:** Never update just one without the other.
