---
name: Frontend Cookie & Rendering
description: 4 cookie variables, ColdFusion cfparam pattern, masterfn/companyfn flow, markdown rendering
type: project
originSessionId: f63f54d9-5d34-44e5-9bb2-c7fa26764c3f
---
**How to apply:** When modifying any frontend file (ai_assistant.cfm, widget, chatbox.html).

## 4 Cookie Variables (all frontends)
| Cookie | Default | Purpose |
|---|---|---|
| `cookie.cookuserloginid` | `user_001` | User identifier |
| `cookie.cookmfnunique` | `demo2011mfn` | masterfn — client scope |
| `cookie.cookcfnunique` | `p11011004464072155` | companyfn — entity scope |
| `cookie.cooklang` | `english` | Language preference |

## ColdFusion Pattern (ai_assistant.cfm)
```cfml
<cfparam name="cookie.cookuserloginid" default="user_001">
<cfparam name="cookie.cookmfnunique"   default="demo2011mfn">
<cfparam name="cookie.cookcfnunique"   default="p11011004464072155">
<cfparam name="cookie.cooklang"        default="english">
```
Injected as JS constants via `<cfoutput>`: USER_ID, COMPANY_ID, MASTERFN, COMPANYFN, LANG

## Markdown Rendering (marked.js)
- CDN: `https://cdn.jsdelivr.net/npm/marked/marked.min.js`
- `renderMarkdown(text)` helper — used in `addBotMessage()` and after typewriter in `addIntro()`
- Typewriter runs first (plain text), then `d.innerHTML = renderMarkdown(text)` on completion

## SSE Event Rendering
| Event | Renderer | Style |
|---|---|---|
| `status` | `typing.setStatus()` | Fade animation |
| `intro` | `addIntro()` → typewriter → markdown | Normal bubble text |
| `step` | `addStep()` → typewriter | Numbered, queued |
| `closing` | `addClosing()` | border-top, #555, 13px — same for RAG and data_query |
| `done` | `tryFinalize()` → feedback buttons | `introText` fallback when no steps |

## introText Fallback
When data_query path returns no steps (only intro+closing), `introText` is captured from the intro event and used as the feedback answer text in `tryFinalize()`.
