# Globe3 ERP — UI Style Guide

Tài liệu này là bộ quy tắc thiết kế cho **tất cả layout** thuộc hệ thống Globe3 ERP AI.  
Mọi giao diện mới đều phải tuân theo các rule dưới đây để đảm bảo đồng bộ với ERP.

> **File tham chiếu:** `style_erp.png` (screenshot giao diện ERP gốc)  
> **File CSS reusable:** `globe3-ui.css` (import vào layout mới thay vì viết lại từ đầu)

---

## 1. Màu sắc (Color Palette)

### Primary

| Token | Hex | Dùng cho |
|---|---|---|
| `--g3-primary` | `#1e3a6e` | Button, avatar bot, icon accent, border focus |
| `--g3-primary-dark` | `#142c57` | Hover / pressed state của primary |
| `--g3-primary-light` | `#e8edf8` | Hover background, selected item, avatar user |

### Backgrounds

| Token | Hex | Dùng cho |
|---|---|---|
| `--g3-bg-page` | `#eaeff7` | Nền tổng thể trang |
| `--g3-bg-white` | `#ffffff` | Card, panel, input, lightbox |
| `--g3-bg-bot` | `#f0f4fb` | Bot message bubble |
| `--g3-bg-panel` | `#f5f8fd` | Panel phụ (feedback box, label) |

### Text

| Token | Hex | Dùng cho |
|---|---|---|
| `--g3-text` | `#1e3a6e` | Tiêu đề, nội dung chính |
| `--g3-text-soft` | `#2d4a7a` | Nội dung phụ, mô tả |
| `--g3-text-muted` | `#8a9bb5` | Timestamp, placeholder, label phụ |
| `--g3-text-on-dark` | `#ffffff` | Text trên nền navy (button, badge) |

### Status (không đổi thành navy)

| Token | Hex | Dùng cho |
|---|---|---|
| `--g3-success` | `#34a853` | Confirmed, thumbs-up |
| `--g3-danger` | `#e53935` | Warning badge, alert icon |

### Rules màu sắc

- **Không dùng** màu xanh Google (`#1a73e8`) — đây là màu cũ, không thuộc Globe3
- **Không dùng** màu xám trung tính (`#f1f3f4`, `#e0e0e0`, `#888`) — thay bằng navy-tinted equivalents
- `--g3-success` và `--g3-danger` **được giữ nguyên** vì là màu status universal
- Mọi interactive element (button, link, focus) đều phải dùng `--g3-primary`

---

## 2. Typography

```css
font-family: system-ui, 'Segoe UI', Arial, sans-serif;
```

| Loại | Size | Weight | Color |
|---|---|---|---|
| Tiêu đề / heading | `15px` | `700` | `--g3-text` |
| Label / tag | `11px` | `600` | `--g3-text` + uppercase + letter-spacing |
| Body text | `13px` | `400` | `--g3-text-soft` |
| Muted / phụ | `11px` | `400` | `--g3-text-muted` |
| Caption / timestamp | `10px` | `400` | `--g3-text-muted` |

- **Font mặc định:** `system-ui, 'Segoe UI', Arial, sans-serif`
- `line-height: 1.65` cho body text
- Menu / section header: ALL CAPS + `letter-spacing: 0.05em`

---

## 3. Spacing

| Token | Value | Dùng cho |
|---|---|---|
| `--g3-space-xs` | `4px` | Gap icon–text, padding badge |
| `--g3-space-sm` | `8px` | Gap giữa elements trong group |
| `--g3-space-md` | `12px` | Padding panel, padding input area |
| `--g3-space-lg` | `16px` | Margin giữa sections |
| `--g3-space-xl` | `24px` | Padding card lớn |

---

## 4. Border & Shadow

```css
border: 1px solid #d0d9ea;              /* --g3-border */
box-shadow: 0 4px 24px rgba(30,58,110,0.10);   /* card nổi */
box-shadow: 0 2px 8px rgba(30,58,110,0.08);    /* dropdown, tooltip */
```

- Mọi card, panel, input, bubble bot đều có `1px solid --g3-border`
- User bubble không có border (nền navy đủ rõ)
- Focus state: `border-color: --g3-primary`
- Shadow luôn dùng màu navy — **không dùng** `rgba(0,0,0,...)`

---

## 5. Border Radius

| Token | Value | Dùng cho |
|---|---|---|
| `--g3-radius-sm` | `6px` | Tag, badge |
| `--g3-radius-md` | `10px` | Feedback panel, small card |
| `--g3-radius-lg` | `12px` | Main card, standalone container |
| `--g3-radius-pill` | `20px` | Input text, chip button |
| `--g3-radius-bubble` | `18px` | Chat bubble |
| `--g3-radius-circle` | `50%` | Avatar |

- Bot bubble: `border-bottom-left-radius: 4px`
- User bubble: `border-bottom-right-radius: 4px`
- Standalone container: `border-radius: 12px` + `overflow: hidden`
- Embedded container: **KHÔNG dùng** `border-radius`

---

## 6. Components

### Chat Bubble
```css
/* Bot */
background: #f0f4fb; color: #1e3a6e;
border: 1px solid #d0d9ea;
border-radius: 18px; border-bottom-left-radius: 4px;

/* User */
background: #1e3a6e; color: white;
border-radius: 18px; border-bottom-right-radius: 4px;
```

### Button
| Loại | Style |
|---|---|
| Primary | Nền `#1e3a6e`, text trắng |
| Ghost | Transparent, viền `#d0d9ea`, hover → navy tint |
| Icon tròn | Circle 38px, nền navy |

### Input
```css
border: 1.5px solid #d0d9ea; border-radius: 20px;
padding: 8px 14px; font-size: 13px;
/* focus: */ border-color: #1e3a6e;
```

### Badge
```css
/* Danger */ background: #e53935; color: white; font-weight: 700;
/* Primary */ background: #1e3a6e; color: white;
/* Muted */ background: #f5f8fd; color: #8a9bb5; border: 1px solid #d0d9ea;
```

---

## 7. Layout Rules

### Standalone (chatbox.html)
```css
body { background: #eaeff7; }
.container { max-width: 860px; margin: 0 auto; height: 100vh;
  background: white; border: 1px solid #d0d9ea;
  border-radius: 12px; box-shadow: 0 4px 24px rgba(30,58,110,0.10); }
```

### Embedded (ai_assistant.cfm)
```css
.container { width: 100%; height: 100vh; background: white;
  /* KHÔNG border-radius, KHÔNG max-width, KHÔNG shadow */ }
```

### Scrollbar
```css
scrollbar-width: thin;
scrollbar-color: #b0bedc #f0f4fb;
```

---

## 8. Hover & Interaction States

| State | Quy tắc |
|---|---|
| Hover primary button | `background: #142c57` |
| Hover ghost/chip | `background: #e8edf8; border-color: #1e3a6e; color: #1e3a6e` |
| Focus input | `border-color: #1e3a6e` |
| Selected item | `background: #e8edf8; color: #1e3a6e` |
| Disabled | `background: #b0bedc; cursor: not-allowed` |
| Transition | `all 0.15s ease` |

---

## 9. Quy trình áp dụng layout mới

1. Import `globe3-ui.css`
2. Dùng `var(--g3-*)` thay vì hardcode màu
3. Dùng class `.g3-*` nếu phù hợp
4. Extend bằng cách override variable — không viết màu mới
5. Kiểm tra bằng cách mở cạnh `style_erp.png`

---

## 10. Checklist trước khi deploy

- [ ] Background: `#eaeff7`
- [ ] Font: `system-ui, 'Segoe UI', Arial`
- [ ] Primary: `#1e3a6e` (không `#1a73e8`)
- [ ] Mọi card/panel: `border: 1px solid #d0d9ea`
- [ ] Bot bubble: border + nền `#f0f4fb`
- [ ] Input focus: `border-color: #1e3a6e`
- [ ] Disabled: `#b0bedc`
- [ ] Shadow: navy color, không đen
- [ ] Standalone: `border-radius: 12px`
- [ ] Embedded: KHÔNG `border-radius`
