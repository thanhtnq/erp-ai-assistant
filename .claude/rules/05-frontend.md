---
description: Frontend templates, standalone vs embedded layout rules, bot avatar, widget button
alwaysApply: true
---

# Frontend

## Templates

| File | Mode | Notes |
|---|---|---|
| `chatbox.html` | Standalone | Floating card, `max-width: 860px`, `border-radius: 12px` |
| `ai_assistant.cfm` | Embedded | Full-width iframe, no border-radius, no shadow |
| `widget_ai_assistant.cfm` | Widget | Floating button + slide-up panel |
| `admin_dashboard.cfm` | Admin | Full-width, horizontal tab strip — no sidebar |

## Standalone vs Embedded CSS

```css
/* chatbox.html */
#chat-container {
  max-width: 860px; margin: 0 auto;
  border-radius: 12px; overflow: hidden;
  border: 1px solid #d0d9ea;
  box-shadow: 0 4px 24px rgba(30,58,110,0.12);
}

/* ai_assistant.cfm */
#chat-container {
  width: 100%; height: 100vh;
  /* NO border-radius, NO max-width, NO shadow */
}
```

## Bot Avatar

- File: `logo.png` — transparent PNG, red robot on clear background
- **Never use** emoji `🤖` or navy background for bot avatar

```css
.bot-avatar { background: none; }
.bot-avatar img { width: 100%; height: 100%; object-fit: contain; border-radius: 6px; display: block; }
```

JS: `'<img src="logo.png" alt="ERP Assistant">'` — no crop, no circle

## Widget Floating Button (`widget_ai_assistant.cfm`)

Logo floats directly — no background, no shadow, no border-radius:

```css
#ai-chat-btn {
  position: fixed; bottom: 20px; right: 20px;
  width: 72px; height: 72px;
  background: none; border: none; cursor: pointer; padding: 0;
  z-index: 99999; transition: transform 0.2s;
}
#ai-chat-btn:hover { transform: scale(1.1); }
```

- When chat is open: show `✕` in `#1e3a6e` instead of logo
- `#ai-chat-wrapper`: `bottom: 104px; right: 20px` (clears the 72px button)
- `#ai-unread-badge`: `bottom: 82px; right: 14px`
