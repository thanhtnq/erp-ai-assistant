---
description: Globe3 design system — colors, typography, spacing, components. Apply to all UI work.
alwaysApply: true
---

# UI Design System

Full reference: `.claude/STYLE_GUIDE.md`  
CSS file: `globe3-ui.css` — import into every new layout, use `var(--g3-*)` classes.

## Color Palette

| Token | Hex | Usage |
|---|---|---|
| `--g3-primary` | `#1e3a6e` | Button, avatar, border focus, user bubble |
| `--g3-primary-dark` | `#142c57` | Hover/pressed state |
| `--g3-primary-light` | `#e8edf8` | Hover bg, selected, user avatar bg |
| `--g3-bg-page` | `#eaeff7` | Overall page background |
| `--g3-bg-bot` | `#f0f4fb` | Bot message bubble bg |
| `--g3-border` | `#d0d9ea` | All borders: card, input, bot bubble |
| `--g3-text-muted` | `#8a9bb5` | Timestamp, placeholder, secondary label |
| `--g3-success` | `#34a853` | Confirmed, thumbs-up |
| `--g3-danger` | `#e53935` | Warning badge, alert |

## Hard Rules

- **Never use** Google Blue `#1a73e8` — old color, not Globe3
- **Never use** neutral gray (`#f1f3f4`, `#888`, `#ccc`) — use navy-tinted equivalents
- Shadow: always `rgba(30,58,110,...)` — never `rgba(0,0,0,...)`
- Disabled: `#b0bedc` — never `#ccc`
- Bot bubble: must have `border: 1px solid #d0d9ea` to distinguish from white bg
- Font: `system-ui, 'Segoe UI', Arial, sans-serif`

## Key Components

**Chat bubble:**
```css
/* Bot */  background: #f0f4fb; border: 1px solid #d0d9ea;
           border-radius: 18px; border-bottom-left-radius: 4px;
/* User */ background: #1e3a6e; color: white;
           border-radius: 18px; border-bottom-right-radius: 4px;
```

**Input:** `border: 1.5px solid #d0d9ea; border-radius: 20px; focus → border-color: #1e3a6e`

**Hover states:** `background: #e8edf8; border-color: #1e3a6e; color: #1e3a6e; transition: all 0.15s ease`

## Deploy Checklist

- [ ] Background: `#eaeff7`
- [ ] Font: `system-ui, 'Segoe UI', Arial`
- [ ] Primary: `#1e3a6e` (not `#1a73e8`)
- [ ] Every card/panel: `border: 1px solid #d0d9ea`
- [ ] Bot bubble: border + `#f0f4fb` bg
- [ ] Standalone container: `border-radius: 12px`
- [ ] Embedded container: no border-radius
- [ ] Shadow: navy color, not black
