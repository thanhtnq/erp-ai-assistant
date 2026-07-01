<!---@ ###########################################################################################################
Version 5.0.1
File Description:
No	Modified Date	Modified By		Change Log
1.	20240701	Lopper		Creation Of File 
################################################################################################################# @--->
<cfset adminUserId  = (structKeyExists(cookie, "cookuserloginid") ? cookie.cookuserloginid : "admin")>
<cfset adminCompany = (structKeyExists(cookie, "cookmfnunique")   ? cookie.cookmfnunique   : "")>
<cfscript>
aiApiUrl = "http://g3rag2.globe3cloud.com:8297";
aiApiKey = "";
envPath = "";
envCandidates = [
  "D:\Job\WebQuanLy\erp-ai-assistant\.env",
  ExpandPath("erp-ai-assistant/.env"),
  ExpandPath("../erp-ai-assistant/.env"),
  ExpandPath("../.env")
];
for (candidate in envCandidates) {
  if (FileExists(candidate)) {
    envPath = candidate;
    break;
  }
}

if (Len(envPath) && FileExists(envPath)) {
  envText = FileRead(envPath);
  envLines = ListToArray(envText, Chr(10));

  for (envLine in envLines) {
    line = Trim(Replace(envLine, Chr(13), "", "all"));
    if (!Len(line) || Left(line, 1) == "##" || !Find("=", line)) {
      continue;
    }

    key = Trim(ListFirst(line, "="));
    value = Trim(Mid(line, Find("=", line) + 1, Len(line)));

    if (Len(value) >= 2) {
      quote = Left(value, 1);
      if ((quote == """" || quote == "'") && Right(value, 1) == quote) {
        value = Mid(value, 2, Len(value) - 2);
      }
    }

    if (key == "CHAT_API_KEY") {
      aiApiKey = value;
    } else if (key == "AI_API_URL") {
      aiApiUrl = value;
    }
  }
}

if (!Len(aiApiKey)) {
  aiApiKey = "YJfgXD-P5WF9p3VCT1XN_ehsnB2KK_OfIYedBxz_J8M";
}
</cfscript>
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Globe3 AI Admin</title>
  <style>
    /* ═══════════════════════════════════════════════════════════════
       Globe3 UI Design Tokens & Utility Classes
       ═══════════════════════════════════════════════════════════════ */

    /* ── 1. DESIGN TOKENS ── */
    :root {
      --g3-primary:       #002b63;
      --g3-primary-dark:  #001f49;
      --g3-primary-light: #eaf1fb;
      --g3-bg-page:       #eaeff7;
      --g3-bg-white:      #ffffff;
      --g3-bg-bot:        #f0f4fb;
      --g3-bg-panel:      #f5f8fd;
      --g3-text:          #1e3a6e;
      --g3-text-soft:     #28466f;
      --g3-text-muted:    #6f829f;
      --g3-text-on-dark:  #ffffff;
      --g3-border:        #d0d9ea;
      --g3-border-strong: #b9c8de;
      --g3-border-focus:  #002b63;
      --g3-success:       #34a853;
      --g3-success-light: #e6f4ea;
      --g3-danger:        #e53935;
      --g3-danger-light:  #fdecea;
      --g3-shadow-card:   0 1px 4px rgba(30,58,110,0.04);
      --g3-shadow-panel:  0 2px 10px rgba(30,58,110,0.10);
      --g3-radius-sm:     4px;
      --g3-radius-md:     8px;
      --g3-radius-lg:     12px;
      --g3-radius-pill:   20px;
      --g3-radius-bubble: 18px;
      --g3-radius-circle: 50%;
      --g3-space-xs:      4px;
      --g3-space-sm:      8px;
      --g3-space-md:      12px;
      --g3-space-lg:      16px;
      --g3-space-xl:      24px;
      --g3-font:          'Century Gothic', CenturyGothic, AppleGothic, sans-serif;
      --g3-font-size-base: 13px;
      --g3-font-size-sm:  11px;
      --g3-font-size-xs:  10px;
      --g3-line-height:   1.65;
      --g3-transition:    all 0.15s ease;
    }

    *, *::before, *::after {
      box-sizing: border-box;
      margin: 0;
      padding: 0;
      font-family: var(--g3-font);
    }

    body {
      background: var(--g3-bg-page);
      color: var(--g3-text);
      font-size: var(--g3-font-size-base);
      line-height: var(--g3-line-height);
      -webkit-font-smoothing: antialiased;
    }

    .g3-card {
      background: var(--g3-bg-white);
      border: 1px solid var(--g3-border);
      border-radius: var(--g3-radius-lg);
      box-shadow: var(--g3-shadow-card);
      overflow: hidden;
    }

    .g3-panel {
      background: var(--g3-bg-panel);
      border: 1px solid var(--g3-border);
      border-radius: var(--g3-radius-md);
      padding: var(--g3-space-md);
    }

    .g3-card-centered {
      max-width: 860px;
      margin: 0 auto;
    }

    .g3-title {
      font-size: 15px;
      font-weight: 700;
      color: var(--g3-text);
      letter-spacing: 0.02em;
    }

    .g3-label {
      font-size: var(--g3-font-size-sm);
      font-weight: 600;
      color: var(--g3-text);
      text-transform: uppercase;
      letter-spacing: 0.05em;
    }

    .g3-body {
      font-size: var(--g3-font-size-base);
      color: var(--g3-text-soft);
      line-height: var(--g3-line-height);
    }

    .g3-muted {
      font-size: var(--g3-font-size-sm);
      color: var(--g3-text-muted);
    }

    .g3-caption {
      font-size: var(--g3-font-size-xs);
      color: var(--g3-text-muted);
    }

    .g3-btn-primary {
      display: inline-flex;
      align-items: center;
      gap: var(--g3-space-xs);
      padding: 6px 16px;
      background: var(--g3-primary);
      color: var(--g3-text-on-dark);
      border: none;
      border-radius: var(--g3-radius-md);
      font-size: var(--g3-font-size-sm);
      font-weight: 500;
      cursor: pointer;
      transition: var(--g3-transition);
      text-decoration: none;
    }
    .g3-btn-primary:hover { background: var(--g3-primary-dark); }
    .g3-btn-primary:disabled { background: #b0bedc; cursor: not-allowed; }

    .g3-btn-ghost {
      display: inline-flex;
      align-items: center;
      gap: var(--g3-space-xs);
      padding: 5px 14px;
      background: transparent;
      color: var(--g3-text-muted);
      border: 1px solid var(--g3-border);
      border-radius: var(--g3-radius-md);
      font-size: var(--g3-font-size-sm);
      cursor: pointer;
      transition: var(--g3-transition);
    }
    .g3-btn-ghost:hover {
      background: var(--g3-primary-light);
      border-color: var(--g3-primary);
      color: var(--g3-primary);
    }

    .g3-btn-icon {
      width: 38px;
      height: 38px;
      background: var(--g3-primary);
      color: var(--g3-text-on-dark);
      border: none;
      border-radius: var(--g3-radius-circle);
      display: flex;
      align-items: center;
      justify-content: center;
      cursor: pointer;
      flex-shrink: 0;
      transition: var(--g3-transition);
    }
    .g3-btn-icon:hover    { background: var(--g3-primary-dark); }
    .g3-btn-icon:disabled { background: #b0bedc; cursor: not-allowed; }
    .g3-btn-icon svg      { width: 16px; height: 16px; fill: currentColor; }

    .g3-chip {
      display: inline-flex;
      align-items: center;
      gap: var(--g3-space-xs);
      padding: 3px 10px;
      border: 1px solid var(--g3-border);
      border-radius: var(--g3-radius-pill);
      background: var(--g3-bg-white);
      color: var(--g3-text-muted);
      font-size: var(--g3-font-size-sm);
      cursor: pointer;
      transition: var(--g3-transition);
    }
    .g3-chip:hover         { background: var(--g3-primary-light); border-color: var(--g3-primary); color: var(--g3-primary); }
    .g3-chip.confirmed     { background: var(--g3-success-light); border-color: var(--g3-success); color: var(--g3-success); pointer-events: none; }
    .g3-chip.dismissed     { display: none; }

    .g3-input,
    .g3-textarea {
      width: 100%;
      border: 1.5px solid var(--g3-border);
      border-radius: var(--g3-radius-pill);
      padding: 8px 14px;
      font-size: var(--g3-font-size-base);
      font-family: var(--g3-font);
      color: var(--g3-text);
      background: var(--g3-bg-white);
      outline: none;
      transition: border-color 0.15s;
    }
    .g3-input:focus,
    .g3-textarea:focus    { border-color: var(--g3-border-focus); }
    .g3-input::placeholder,
    .g3-textarea::placeholder { color: var(--g3-text-muted); }

    .g3-textarea {
      border-radius: var(--g3-radius-sm);
      resize: none;
      line-height: var(--g3-line-height);
    }

    input[type="radio"],
    input[type="checkbox"] {
      accent-color: var(--g3-primary);
      cursor: pointer;
    }

    .g3-avatar {
      width: 28px;
      height: 28px;
      border-radius: var(--g3-radius-circle);
      flex-shrink: 0;
      display: flex;
      align-items: center;
      justify-content: center;
      font-size: 11px;
      font-weight: 700;
      overflow: hidden;
    }
    .g3-avatar-bot  { background: var(--g3-primary); color: var(--g3-text-on-dark); }
    .g3-avatar-user { background: var(--g3-primary-light); color: var(--g3-primary); }
    .g3-avatar img  { width: 100%; height: 100%; object-fit: cover; border-radius: var(--g3-radius-circle); }

    .g3-bubble {
      padding: 9px 13px;
      border-radius: var(--g3-bubble-radius, var(--g3-radius-bubble));
      font-size: var(--g3-font-size-base);
      line-height: var(--g3-line-height);
      word-break: break-word;
    }

    .g3-bubble-bot {
      background: var(--g3-bg-bot);
      color: var(--g3-text);
      border: 1px solid var(--g3-border);
      border-bottom-left-radius: 4px;
    }

    .g3-bubble-user {
      background: var(--g3-primary);
      color: var(--g3-text-on-dark);
      border-bottom-right-radius: 4px;
    }

    .g3-divider {
      border: none;
      border-top: 1px solid var(--g3-border);
      margin: var(--g3-space-md) 0;
    }

    .g3-date-sep {
      text-align: center;
      font-size: var(--g3-font-size-xs);
      color: var(--g3-text-muted);
      margin: 6px 0;
      position: relative;
      user-select: none;
    }
    .g3-date-sep::before,
    .g3-date-sep::after {
      content: "";
      position: absolute;
      top: 50%;
      width: 25%;
      height: 1px;
      background: var(--g3-border);
    }
    .g3-date-sep::before { left: 0; }
    .g3-date-sep::after  { right: 0; }

    .g3-badge {
      display: inline-flex;
      align-items: center;
      padding: 2px 8px;
      border-radius: var(--g3-radius-sm);
      font-size: var(--g3-font-size-sm);
      font-weight: 600;
      letter-spacing: 0.04em;
    }
    .g3-badge-danger   { background: var(--g3-danger);        color: white; }
    .g3-badge-primary  { background: var(--g3-primary);       color: white; }
    .g3-badge-success  { background: var(--g3-success);       color: white; }
    .g3-badge-muted    { background: var(--g3-bg-panel);      color: var(--g3-text-muted); border: 1px solid var(--g3-border); }

    .g3-spinner {
      border-radius: var(--g3-radius-circle);
      border: 3px solid var(--g3-primary-light);
      border-top-color: var(--g3-primary);
      animation: g3-spin 0.8s linear infinite;
    }
    .g3-spinner-sm { width: 16px; height: 16px; border-width: 2px; }
    .g3-spinner-md { width: 26px; height: 26px; border-width: 3px; }
    .g3-spinner-lg { width: 40px; height: 40px; border-width: 4px; }

    @keyframes g3-spin { to { transform: rotate(360deg); } }

    .g3-scroll {
      overflow-y: auto;
      scrollbar-width: thin;
      scrollbar-color: #b0bedc var(--g3-bg-bot);
    }
    .g3-scroll::-webkit-scrollbar       { width: 6px; }
    .g3-scroll::-webkit-scrollbar-track { background: var(--g3-bg-bot); }
    .g3-scroll::-webkit-scrollbar-thumb { background: #b0bedc; border-radius: 3px; }

    @keyframes g3-fadeIn {
      from { opacity: 0; transform: translateY(-4px); }
      to   { opacity: 1; transform: translateY(0); }
    }

    @keyframes g3-slideUp {
      from { opacity: 0; transform: translateY(5px); }
      to   { opacity: 1; transform: translateY(0); }
    }

    @keyframes g3-blink {
      0%, 100% { opacity: 1; }
      50%       { opacity: 0; }
    }

    .g3-anim-fadeIn  { animation: g3-fadeIn  0.15s ease; }
    .g3-anim-slideUp { animation: g3-slideUp 0.2s  ease; }
  </style>
  <script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.0/dist/chart.umd.min.js"></script>
  <style>
    *, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }

    body {
      font-family: var(--g3-font);
      font-size: var(--g3-font-size-base);
      background: #fff;
      color: var(--g3-text);
      min-height: 100vh;
      display: flex;
      flex-direction: column;
    }

    /* ── Page Header (matches ERP dashboard header style) ── */
    #page-header {
      padding: 16px 24px 0;
      background: #fff;
      border-bottom: 1px solid var(--g3-border);
    }
    .page-module-label {
      font-size: 11px;
      font-weight: 700;
      text-transform: uppercase;
      letter-spacing: 0.1em;
      color: var(--g3-text-muted);
      margin-bottom: 4px;
    }
    .page-title-row {
      display: flex;
      align-items: flex-end;
      justify-content: space-between;
      gap: 12px;
      margin-bottom: 14px;
    }
    .page-title {
      font-size: 22px;
      font-weight: 700;
      color: var(--g3-primary);
      letter-spacing: 0.01em;
      display: flex;
      align-items: center;
      gap: 10px;
    }
    .page-title img { width: 28px; height: 28px; object-fit: contain; }
    .page-meta {
      font-size: 12px;
      color: var(--g3-text-muted);
      padding-bottom: 2px;
    }

    /* ── Module Tab Strip (like ERP's orange tab bar, in Globe3 navy) ── */
    #module-tabs {
      display: flex;
      align-items: flex-end;
      gap: 0;
    }
    .mod-tab {
      padding: 10px 22px;
      font-size: 12px;
      font-weight: 700;
      text-transform: uppercase;
      letter-spacing: 0.06em;
      cursor: pointer;
      border: none;
      background: none;
      font-family: var(--g3-font);
      color: var(--g3-text-muted);
      border-bottom: 3px solid transparent;
      margin-bottom: -1px;
      transition: var(--g3-transition);
      white-space: nowrap;
      display: flex;
      align-items: center;
      gap: 7px;
      position: relative;
    }
    .mod-tab:hover { color: var(--g3-primary); background: var(--g3-primary-light); }
    .mod-tab.active {
      color: var(--g3-primary);
      border-bottom-color: var(--g3-primary);
      background: var(--g3-primary-light);
    }
    .mod-tab.disabled {
      opacity: 0.4;
      cursor: not-allowed;
      pointer-events: none;
    }
    .mod-tab .tab-badge {
      background: var(--g3-danger);
      color: #fff;
      font-size: 10px;
      font-weight: 700;
      border-radius: 10px;
      padding: 1px 6px;
      min-width: 18px;
      text-align: center;
    }
    .mod-tab .tab-soon {
      font-size: 9px;
      font-weight: 400;
      text-transform: none;
      letter-spacing: 0;
      color: var(--g3-text-muted);
      font-style: italic;
    }

    /* ── Main Content Area ── */
    #content {
      flex: 1;
      padding: 20px 24px 32px;
      background: #f5f8fd;
      min-height: 0;
    }

    /* ── Section within a tab ── */
    .tab-panel { display: none; }
    .tab-panel.active { display: block; }

    /* ── KPI Stats Row — flex auto-sized (no full-width), no border, large label ── */
    .kpi-row {
      display: flex;
      flex-wrap: wrap;
      gap: 14px;
      margin-bottom: 24px;
    }
    .kpi-card {
      background: #fff;
      border-radius: 8px;
      padding: 18px 22px 20px;
      display: flex;
      flex-direction: column;
      gap: 0;
      box-shadow: 0 2px 10px rgba(30,58,110,0.10);
      flex: 0 0 auto;
      min-width: 300px;
    }
    .kpi-label {
      font-size: 12px;
      font-weight: 800;
      text-transform: uppercase;
      letter-spacing: 0.06em;
      color: #5a6e8a;
      margin-bottom: 12px;
    }
    .kpi-body { display: flex; align-items: center; gap: 16px; }
    /* Rounded-square icon */
    .kpi-icon {
      width: 62px; height: 62px;
      border-radius: 12px;
      background: var(--g3-primary);
      display: flex; align-items: center; justify-content: center;
      flex-shrink: 0;
    }
    .kpi-icon.navy  { background: #1e3a6e; }
    .kpi-icon.blue  { background: #2e6fd9; }
    .kpi-icon.green { background: var(--g3-success); }
    .kpi-icon.red   { background: var(--g3-danger); }
    .kpi-icon.light { background: var(--g3-primary-light); }
    /* White symbol on colored icon */
    .kpi-sym { font-size: 28px; line-height: 1; color: #fff; font-weight: 700; }
    .kpi-icon.light .kpi-sym { color: var(--g3-primary); }
    .kpi-nums { flex: 1; min-width: 0; }
    .kpi-info { flex: 1; min-width: 0; } /* keep for JS compat */
    .kpi-value {
      font-size: 42px;
      font-weight: 700;
      color: var(--g3-text);
      line-height: 1;
    }
    .kpi-value.danger  { color: var(--g3-danger); }
    .kpi-value.success { color: var(--g3-success); }
    .kpi-sub {
      font-size: 11px;
      color: var(--g3-text-muted);
      margin-top: 6px;
    }

    /* ── Content Card (white panel) ── */
    .content-card {
      background: #fff;
      border: 1px solid var(--g3-border);
      border-radius: 8px;
      overflow: hidden;
      margin-bottom: 16px;
      box-shadow: 0 1px 4px rgba(30,58,110,0.04);
    }
    .content-card-header {
      padding: 12px 16px;
      border-bottom: 1px solid var(--g3-border);
      display: flex;
      align-items: center;
      gap: 12px;
      background: #fff;
    }
    .content-card-title {
      font-size: 13px;
      font-weight: 700;
      color: var(--g3-text);
      flex: 1;
    }
    .content-card-body { padding: 14px 16px; }

    /* ── Sub-tabs sit directly on the page — exact match ERP Approval Dashboard ── */
    .sub-tab-area {
      display: flex;
      align-items: flex-end;
      justify-content: space-between;
      border-bottom: 2px solid var(--g3-border);
      margin-bottom: 16px;
    }
    .sub-tab-row {
      display: flex;
      align-items: flex-end;
      gap: 0;
    }
    .sub-tab {
      padding: 8px 22px 10px;
      font-size: 13px;
      font-weight: 600;
      cursor: pointer;
      border: none;
      border-bottom: 2px solid transparent;
      margin-bottom: -2px;
      background: none;
      font-family: var(--g3-font);
      color: var(--g3-text-muted);
      transition: var(--g3-transition);
      display: flex;
      align-items: center;
      gap: 7px;
    }
    .sub-tab:hover { color: var(--g3-primary); }
    .sub-tab.active {
      color: var(--g3-primary);
      font-weight: 700;
      border-bottom-color: var(--g3-primary);
    }
    .sub-tab .sub-badge {
      background: var(--g3-danger);
      color: #fff;
      font-size: 10px;
      border-radius: 10px;
      padding: 1px 6px;
      font-weight: 700;
    }

    /* ── Filter Bar ── */
    .filter-bar {
      display: flex;
      align-items: center;
      gap: 8px;
      margin-bottom: 14px;
      flex-wrap: wrap;
    }
    .filter-bar select,
    .filter-bar input[type="date"] {
      font-family: var(--g3-font);
      font-size: 12px;
      height: 32px;
      padding: 0 10px;
      border: 1px solid var(--g3-border);
      border-radius: 4px;
      background: #fff;
      color: var(--g3-text);
      outline: none;
      cursor: pointer;
      transition: var(--g3-transition);
    }
    .filter-bar select:focus,
    .filter-bar input:focus { border-color: var(--g3-primary); }
    .filter-spacer { flex: 1; }
    .btn-sm {
      height: 32px; padding: 0 14px;
      font-size: 12px; font-weight: 600; font-family: var(--g3-font);
      border-radius: 4px; cursor: pointer; transition: var(--g3-transition);
      border: 1px solid var(--g3-border); background: #fff; color: var(--g3-text);
    }
    .btn-sm:hover { border-color: var(--g3-primary); color: var(--g3-primary); background: var(--g3-primary-light); }
    .btn-sm.primary { background: var(--g3-primary); color: #fff; border-color: var(--g3-primary); }
    .btn-sm.primary:hover { background: var(--g3-primary-dark); }

    /* ── Feedback Cards ── */
    .feedback-list { display: flex; flex-direction: column; gap: 6px; }

    .fb-card {
      border: 1px solid var(--g3-border);
      border-radius: 6px;
      background: #fff;
      overflow: hidden;
      transition: border-color 0.15s;
    }
    .fb-card:hover { border-color: #b0bedc; }
    .fb-card.open  { border-color: #b0bedc; background: #fafcff; }
    .fb-card.flag-pending  { border-left: 3px solid var(--g3-danger); }
    .fb-card.flag-resolved { border-left: 3px solid var(--g3-success); }

    .fb-row {
      display: flex;
      align-items: center;
      gap: 10px;
      padding: 10px 14px;
      cursor: pointer;
      user-select: none;
    }
    .fb-row:hover { background: #f5f8fd; }

    .fb-icon { font-size: 16px; flex-shrink: 0; }
    .fb-main { flex: 1; min-width: 0; }
    .fb-name {
      font-size: 13px; font-weight: 600; color: var(--g3-text);
      white-space: nowrap; overflow: hidden; text-overflow: ellipsis;
      display: flex; align-items: center; gap: 7px;
    }
    .fb-crumb { font-size: 11px; color: var(--g3-text-muted); margin-top: 1px; }
    .fb-right { display: flex; align-items: center; gap: 8px; flex-shrink: 0; }
    .fb-chevron { font-size: 10px; color: var(--g3-text-muted); transition: transform 0.15s; }
    .fb-card.open .fb-chevron { transform: rotate(90deg); }

    /* ── Icon action buttons — in collapsed row, between date and chevron ── */
    .fb-row-btns { display: flex; align-items: center; gap: 2px; }
    .fb-icon-btn {
      width: 28px; height: 28px;
      border: none; border-radius: 4px; background: none;
      cursor: pointer; font-size: 15px;
      display: flex; align-items: center; justify-content: center;
      color: var(--g3-text-muted);
      transition: background 0.15s, transform 0.12s, color 0.15s;
      line-height: 1;
    }
    .fb-icon-btn:hover { background: var(--g3-primary-light); color: var(--g3-primary); transform: scale(1.15); }
    .fb-icon-btn.flag-btn:hover    { background: #fff3e0; color: #b35c00; transform: scale(1.15); }
    .fb-icon-btn.resolve-btn:hover { background: #e6f4ea; color: #2d7a3a; transform: scale(1.15); }
    .fb-icon-btn.unflag-btn:hover  { background: #fdecea; color: #c0392b; transform: scale(1.15); }

    .fb-detail {
      display: none;
      padding: 0 14px 14px;
      border-top: 2px solid var(--g3-border);
    }
    .fb-card.open .fb-detail { display: block; }

    .fb-grid {
      display: grid;
      grid-template-columns: 1fr 1fr;
      gap: 10px 24px;
      margin: 12px 0 0;
    }
    .fb-field { }
    .fb-field.span2 { grid-column: 1 / -1; }
    .fb-flabel {
      font-size: 10px; font-weight: 700; text-transform: uppercase;
      letter-spacing: 0.06em; color: var(--g3-text-muted); margin-bottom: 3px;
    }
    .fb-fval { font-size: 12px; color: var(--g3-text-soft); line-height: 1.5; }
    .fb-query {
      background: #f5f8fd; border: 1px solid var(--g3-border);
      border-radius: 4px; padding: 7px 10px;
      font-size: 12px; color: var(--g3-text-soft); font-style: italic;
    }

    /* ── Resolved info banner (read-only, trong expanded detail) ── */
    .resolved-info {
      display: flex; align-items: flex-start; gap: 8px;
      background: #e6f4ea; border: 1px solid #c8e6c9; border-radius: 4px;
      padding: 8px 12px; font-size: 12px; color: #2d7a3a;
      margin: 10px 0 2px;
    }
    .resolved-info strong { color: #1e5c28; }

    .fb-actions { display: flex; gap: 8px; margin-top: 12px; flex-wrap: wrap; }

    .btn-resolve {
      height: 28px; padding: 0 14px; font-size: 11px; font-weight: 700;
      font-family: var(--g3-font); background: var(--g3-success); color: #fff;
      border: none; border-radius: 4px; cursor: pointer; transition: var(--g3-transition);
      text-transform: uppercase; letter-spacing: 0.04em;
    }
    .btn-resolve:hover { background: #2d9248; }
    .btn-unflag {
      height: 28px; padding: 0 14px; font-size: 11px; font-weight: 700;
      font-family: var(--g3-font); background: none; color: var(--g3-danger);
      border: 1px solid var(--g3-danger); border-radius: 4px; cursor: pointer;
      transition: var(--g3-transition); text-transform: uppercase; letter-spacing: 0.04em;
    }
    .btn-unflag:hover { background: var(--g3-danger-light); }
    .btn-view-log {
      height: 28px; padding: 0 14px; font-size: 11px; font-weight: 700;
      font-family: var(--g3-font); background: none; color: var(--g3-primary);
      border: 1px solid var(--g3-border); border-radius: 4px; cursor: pointer;
      transition: var(--g3-transition); text-transform: uppercase; letter-spacing: 0.04em;
    }
    .btn-view-log:hover { border-color: var(--g3-primary); background: var(--g3-primary-light); }
    .btn-flag {
      height: 28px; padding: 0 14px; font-size: 11px; font-weight: 700;
      font-family: var(--g3-font); background: none; color: #b35c00;
      border: 1px solid #f0c080; border-radius: 4px; cursor: pointer;
      transition: var(--g3-transition); text-transform: uppercase; letter-spacing: 0.04em;
    }
    .btn-flag:hover { background: #fff3e0; border-color: #e09020; }

    .resolved-banner {
      display: flex; align-items: flex-start; gap: 8px;
      background: #e6f4ea; border: 1px solid #c8e6c9; border-radius: 4px;
      padding: 8px 12px; font-size: 12px; color: #2d7a3a; margin-top: 10px;
    }

    /* ── Status Badges ── */
    .badge {
      display: inline-block; padding: 2px 8px; border-radius: 3px;
      font-size: 10px; font-weight: 700; text-transform: uppercase;
      letter-spacing: 0.04em; white-space: nowrap;
    }
    .badge-pending  { background: #fdecea; color: var(--g3-danger); }
    .badge-resolved { background: #e6f4ea; color: #2d7a3a; }
    .badge-up       { background: #e6f4ea; color: #2d7a3a; }
    .badge-down     { background: #fdecea; color: var(--g3-danger); }
    .badge-action   { background: #fff3e0; color: #b35c00; }
    .badge-reason   { background: var(--g3-primary-light); color: var(--g3-primary); }

    /* ── Action Log Table ── */
    .log-wrap {
      border-radius: 6px; overflow: hidden;
      border: 1px solid var(--g3-border);
    }
    table.log-tbl {
      width: 100%; border-collapse: collapse; font-size: 12px;
    }
    .log-tbl th {
      background: #f5f8fd; border-bottom: 1px solid var(--g3-border);
      padding: 9px 12px; text-align: left;
      font-size: 10px; font-weight: 700; text-transform: uppercase;
      letter-spacing: 0.06em; color: var(--g3-text-muted); white-space: nowrap;
    }
    .log-tbl td {
      padding: 9px 12px; border-bottom: 1px solid #f0f4fb;
      color: var(--g3-text-soft); vertical-align: top; font-size: 12px;
    }
    .log-tbl tr:last-child td { border-bottom: none; }
    .log-tbl tr:hover td { background: #f5f8fd; }

    .act-badge {
      display: inline-block; padding: 2px 8px; border-radius: 3px;
      font-size: 10px; font-weight: 700; text-transform: uppercase;
      letter-spacing: 0.04em; white-space: nowrap;
    }
    .act-badge.resolve_flag    { background: #e6f4ea; color: #2d7a3a; }
    .act-badge.unflag          { background: #fdecea; color: #c0392b; }
    .act-badge.manual_flag     { background: #fff3e0; color: #b35c00; }
    .act-badge.upload_document { background: var(--g3-primary-light); color: var(--g3-primary); }
    .act-badge.run_ingest      { background: #f3e5f5; color: #6a1b9a; }
    .act-badge.ingest_completed{ background: #e6f4ea; color: #2d7a3a; }
    .act-badge.ingest_failed   { background: #fdecea; color: #c0392b; }
    .act-badge.scheduler_enable     { background: #e6f4ea; color: #2d7a3a; }
    .act-badge.scheduler_disable    { background: #fdecea; color: #c0392b; }
    .act-badge.scheduler_run_now    { background: #f3e5f5; color: #6a1b9a; }
    .act-badge.scheduler_update_time{ background: var(--g3-primary-light); color: var(--g3-primary); }

    /* ── Pagination ── */
    .pag-row {
      display: flex; align-items: center; justify-content: flex-end;
      gap: 6px; padding: 10px 0 0;
    }
    .pag-info { font-size: 12px; color: var(--g3-text-muted); margin-right: 4px; }
    .pag-btn {
      height: 28px; padding: 0 12px; font-size: 11px; font-weight: 600;
      font-family: var(--g3-font); background: #fff;
      border: 1px solid var(--g3-border); border-radius: 4px;
      cursor: pointer; color: var(--g3-text); transition: var(--g3-transition);
    }
    .pag-btn:hover:not(:disabled) { border-color: var(--g3-primary); color: var(--g3-primary); }
    .pag-btn:disabled { opacity: 0.4; cursor: not-allowed; }

    /* ── Empty / Loading ── */
    .state-msg {
      text-align: center; padding: 40px 24px;
      font-size: 13px; color: var(--g3-text-muted);
    }
    .state-loading {
      text-align: center; padding: 40px 24px;
      font-size: 13px; color: var(--g3-text-muted);
    }
    .state-loading::before {
      content: ''; display: block;
      width: 26px; height: 26px;
      border: 3px solid var(--g3-primary-light);
      border-top-color: var(--g3-primary);
      border-radius: 50%; margin: 0 auto 10px;
      animation: spin 0.7s linear infinite;
    }
    @keyframes spin { to { transform: rotate(360deg); } }

    /* ── Modal ── */
    #modal-overlay {
      display: none; position: fixed; inset: 0;
      background: rgba(30,58,110,0.22); z-index: 9000;
      align-items: center; justify-content: center;
    }
    #modal-overlay.open { display: flex; }
    .modal-box {
      background: #fff; border: 1px solid var(--g3-border);
      border-radius: 8px; box-shadow: 0 8px 32px rgba(30,58,110,0.18);
      padding: 24px; width: 460px; max-width: 95vw;
    }
    .modal-title { font-size: 15px; font-weight: 700; color: var(--g3-text); margin-bottom: 6px; }
    .modal-sub   { font-size: 12px; color: var(--g3-text-muted); margin-bottom: 14px; line-height: 1.5; }
    .modal-ta {
      width: 100%; height: 88px; padding: 9px 12px;
      font-family: var(--g3-font); font-size: 13px;
      border: 1px solid var(--g3-border); border-radius: 4px;
      resize: vertical; outline: none; color: var(--g3-text);
      transition: var(--g3-transition);
    }
    .modal-ta:focus { border-color: var(--g3-primary); }
    .modal-err { font-size: 11px; color: var(--g3-danger); margin-top: 4px; display: none; }
    .modal-foot { display: flex; justify-content: flex-end; gap: 8px; margin-top: 16px; }
    .btn-modal-cancel {
      height: 32px; padding: 0 16px; font-size: 12px; font-weight: 600;
      font-family: var(--g3-font); background: #fff;
      border: 1px solid var(--g3-border); border-radius: 4px;
      cursor: pointer; color: var(--g3-text); transition: var(--g3-transition);
    }
    .btn-modal-cancel:hover { border-color: var(--g3-primary); color: var(--g3-primary); }
    .btn-modal-ok {
      height: 32px; padding: 0 18px; font-size: 12px; font-weight: 700;
      font-family: var(--g3-font); background: var(--g3-success); color: #fff;
      border: none; border-radius: 4px; cursor: pointer; transition: var(--g3-transition);
      text-transform: uppercase; letter-spacing: 0.04em;
    }
    .btn-modal-ok:hover:not(:disabled) { background: #2d9248; }
    .btn-modal-ok:disabled { background: #b0bedc; cursor: not-allowed; }

    /* ── Toast ── */
    #toast {
      position: fixed; bottom: 20px; right: 24px;
      background: var(--g3-primary); color: #fff;
      padding: 10px 18px; border-radius: 4px;
      font-size: 12px; font-weight: 600;
      box-shadow: 0 4px 16px rgba(30,58,110,0.25);
      z-index: 9999; opacity: 0; transition: opacity 0.2s;
      pointer-events: none;
    }
    #toast.show  { opacity: 1; }
    #toast.error { background: var(--g3-danger); }

    /* ── Document Status Badges ── */
    .doc-status {
      display: inline-block; padding: 2px 8px; border-radius: 3px;
      font-size: 10px; font-weight: 700; text-transform: uppercase;
      letter-spacing: 0.04em; white-space: nowrap;
    }
    .doc-status.done       { background: #e6f4ea; color: #2d7a3a; }
    .doc-status.failed     { background: #fdecea; color: var(--g3-danger); }
    .doc-status.pending    { background: #fff3e0; color: #b35c00; }
    .doc-status.processing { background: var(--g3-primary-light); color: var(--g3-primary); }
    .doc-progress-wrap { width:100%;height:3px;background:#e8edf8;border-radius:2px;margin-top:5px;overflow:hidden; }
    .doc-progress-bar  { height:100%;width:35%;background:var(--g3-primary);border-radius:2px;animation:docSlide 1.4s ease-in-out infinite; }
    @keyframes docSlide { 0%{transform:translateX(-200%)} 100%{transform:translateX(400%)} }

    /* ── Document error snippet row ── */
    .doc-err-row td {
      background: #fff8f7; padding: 6px 12px 8px 52px;
      border-bottom: 1px solid #f0f4fb;
    }
    .doc-err-snippet {
      background: #fdecea; border-radius: 3px;
      padding: 4px 8px; font-family: monospace; font-size: 10px;
      line-height: 1.5; white-space: pre-wrap; word-break: break-all;
      max-height: 80px; overflow: hidden; color: var(--g3-danger);
    }

    /* ── Text search input in filter bar ── */
    .filter-bar input[type="text"] {
      font-family: var(--g3-font); font-size: 12px;
      height: 32px; padding: 0 10px;
      border: 1px solid var(--g3-border); border-radius: 4px;
      background: #fff; color: var(--g3-text); outline: none;
      min-width: 180px; transition: var(--g3-transition);
    }
    .filter-bar input[type="text"]:focus { border-color: var(--g3-primary); }

    /* ── reingest_queued / clear_feedback action badges ── */
    .act-badge.reingest_queued { background: #fff3e0; color: #b35c00; }
    .act-badge.clear_feedback  { background: #fdecea; color: #c0392b; }

    /* ── Clear Feedback danger button ── */
    .btn-sm.danger {
      color: var(--g3-danger); border-color: var(--g3-danger);
    }
    .btn-sm.danger:hover {
      background: #fdecea; border-color: #c0392b; color: #c0392b;
    }

    /* ── Scheduler Tab ── */
    .sched-grid {
      display: grid;
      grid-template-columns: repeat(auto-fill, minmax(420px, 1fr));
      gap: 16px;
      margin-bottom: 24px;
    }
    .job-card {
      background: #fff;
      border: 1px solid var(--g3-border);
      border-radius: 8px;
      overflow: hidden;
      box-shadow: 0 1px 4px rgba(30,58,110,0.05);
    }
    .job-card-header {
      display: flex;
      align-items: center;
      gap: 10px;
      padding: 14px 16px 12px;
      border-bottom: 1px solid var(--g3-border);
      background: #fff;
    }
    .job-title {
      flex: 1;
      font-size: 14px;
      font-weight: 700;
      color: var(--g3-text);
    }
    .job-badge {
      display: inline-flex;
      align-items: center;
      gap: 5px;
      padding: 3px 10px;
      border-radius: 20px;
      font-size: 11px;
      font-weight: 700;
      text-transform: uppercase;
      letter-spacing: 0.05em;
    }
    .job-badge.enabled  { background: #e6f4ea; color: #2d7a3a; }
    .job-badge.disabled { background: #f5f5f5; color: #8a9bb5; }
    .job-badge.running  { background: var(--g3-primary-light); color: var(--g3-primary); }

    .job-dot {
      width: 8px; height: 8px;
      border-radius: 50%;
      display: inline-block;
    }
    .job-dot.green  { background: #34a853; }
    .job-dot.gray   { background: #b0bedc; }
    .job-dot.pulse  {
      background: var(--g3-primary);
      animation: pulse-dot 1s infinite;
    }
    @keyframes pulse-dot {
      0%,100% { opacity: 1; } 50% { opacity: 0.3; }
    }

    .job-body {
      padding: 14px 16px;
    }
    .job-meta-row {
      display: flex;
      gap: 24px;
      flex-wrap: wrap;
      margin-bottom: 12px;
    }
    .job-meta-item {
      min-width: 0;
    }
    .job-meta-label {
      font-size: 10px;
      font-weight: 700;
      text-transform: uppercase;
      letter-spacing: 0.06em;
      color: var(--g3-text-muted);
      margin-bottom: 2px;
    }
    .job-meta-val {
      font-size: 13px;
      color: var(--g3-text);
      font-weight: 500;
    }
    .job-meta-val.success { color: var(--g3-success); }
    .job-meta-val.failed  { color: var(--g3-danger); }
    .job-meta-val.running { color: var(--g3-primary); }
    .job-meta-val.muted   { color: var(--g3-text-muted); font-style: italic; }

    .job-actions {
      display: flex;
      gap: 8px;
      flex-wrap: wrap;
      padding-top: 12px;
      border-top: 1px solid var(--g3-border);
      margin-top: 12px;
    }

    /* Inline schedule edit form */
    .sched-edit-form {
      display: none;
      background: #f5f8fd;
      border: 1px solid var(--g3-border);
      border-radius: 6px;
      padding: 12px 14px;
      margin-top: 12px;
    }
    .sched-edit-form.open { display: block; }
    .sched-edit-row {
      display: flex;
      align-items: center;
      gap: 8px;
      flex-wrap: wrap;
    }
    .sched-edit-row label {
      font-size: 11px;
      font-weight: 700;
      color: var(--g3-text-muted);
      text-transform: uppercase;
      letter-spacing: 0.05em;
      white-space: nowrap;
    }
    .sched-edit-row select,
    .sched-edit-row input[type="time"] {
      font-family: var(--g3-font);
      font-size: 12px;
      height: 30px;
      padding: 0 8px;
      border: 1px solid var(--g3-border);
      border-radius: 4px;
      background: #fff;
      color: var(--g3-text);
      outline: none;
    }
    .sched-edit-row select:focus,
    .sched-edit-row input:focus { border-color: var(--g3-primary); }

    @media (max-width: 900px) {
      .kpi-row { grid-template-columns: repeat(2, 1fr); }
      .fb-grid  { grid-template-columns: 1fr; }
      .mod-tab .tab-soon { display: none; }
      .sched-grid { grid-template-columns: 1fr; }
    }

    /* ── Knowledge Entry Drawer ── */
    #kb-drawer {
      position: fixed; inset: 0;
      z-index: 2000;
      pointer-events: none;
    }
    #kb-drawer.open { pointer-events: all; }
    #kb-drawer-backdrop {
      position: absolute; inset: 0;
      background: rgba(30,58,110,0.18);
      opacity: 0; transition: opacity 0.25s ease;
    }
    #kb-drawer.open #kb-drawer-backdrop { opacity: 1; }
    #kb-drawer-panel {
      position: absolute; top: 0; right: -500px; bottom: 0;
      width: 500px; background: #fff;
      border-left: 1px solid var(--g3-border);
      box-shadow: -4px 0 24px rgba(30,58,110,0.14);
      display: flex; flex-direction: column;
      transition: right 0.25s ease;
    }
    #kb-drawer.open #kb-drawer-panel { right: 0; }
    #kb-drawer-head {
      display: flex; align-items: center; gap: 12px;
      padding: 14px 16px;
      border-bottom: 1px solid var(--g3-border);
      background: #f5f8fd; flex-shrink: 0;
    }
    #kb-drawer-title {
      font-size: 14px; font-weight: 700;
      color: var(--g3-primary);
      flex: 1; min-width: 0;
      overflow: hidden; text-overflow: ellipsis; white-space: nowrap;
    }
    #kb-drawer-body { flex: 1; overflow-y: auto; padding: 16px; }

    /* kb search input inline style via filter-bar, no extra class needed */
    .kb-search-input {
      height: 32px; padding: 0 10px;
      border: 1px solid var(--g3-border); border-radius: 4px;
      font-family: var(--g3-font); font-size: 12px; width: 220px; outline: none;
      transition: var(--g3-transition);
    }
    .kb-search-input:focus { border-color: var(--g3-primary); }

    /* ── Analytics (Phase 6) ── */
    .anl-chart-row {
      display: grid;
      gap: 14px;
      margin-bottom: 16px;
    }
    .anl-chart-row.cols-2 { grid-template-columns: 1fr 1fr; }
    .anl-chart-row.cols-1 { grid-template-columns: 1fr; }
    .anl-chart-wrap {
      background: #fff;
      border: 1px solid var(--g3-border);
      border-radius: 8px;
      padding: 16px;
      box-shadow: 0 1px 4px rgba(30,58,110,0.04);
    }
    .anl-chart-title {
      font-size: 12px; font-weight: 800; text-transform: uppercase;
      letter-spacing: 0.05em; color: #5a6e8a; margin-bottom: 12px;
    }
    .anl-chart-wrap canvas { max-height: 260px; }
    .anl-query-list { margin: 0; padding-left: 20px; }
    .anl-query-list li {
      font-size: 13px; padding: 5px 0;
      border-bottom: 1px solid var(--g3-border); color: var(--g3-text);
    }
    .anl-query-list li:last-child { border-bottom: none; }
    .anl-query-count {
      font-size: 11px; color: var(--g3-text-muted); margin-left: 6px;
    }
    .anl-note {
      font-size: 11px; color: var(--g3-text-muted);
      margin-bottom: 14px; font-style: italic;
    }
    @media (max-width: 860px) {
      .anl-chart-row.cols-2 { grid-template-columns: 1fr; }
    }
  </style>
</head>
<body>

<!-- ── Page Header ───────────────────────────────────────────── -->
<div id="page-header">
  <div class="page-module-label">AI ASSISTANT</div>
  <div class="page-title-row">
    <div class="page-title">
      <img src="logo.png" alt="">
      AI ADMIN DASHBOARD
    </div>
    <div class="page-meta" id="meta-user"></div>
  </div>

  <!-- Module Tab Strip -->
  <div id="module-tabs">
    <button class="mod-tab active" data-tab="feedback" onclick="switchTab('feedback')">
      Feedback
      <span class="tab-badge" id="tab-badge-pending" style="display:none"></span>
    </button>
    <button class="mod-tab" data-tab="action-log" onclick="switchTab('action-log')">
      Action Log
    </button>
    <button class="mod-tab" data-tab="documents" onclick="switchTab('documents')">
      Documents
    </button>
    <button class="mod-tab" data-tab="scheduler" onclick="switchTab('scheduler')">
      Scheduler
    </button>
    <button class="mod-tab" data-tab="knowledge" onclick="switchTab('knowledge')">
      Knowledge
    </button>
    <button class="mod-tab" data-tab="health" onclick="switchTab('health')">
      Health
    </button>
    <button class="mod-tab" data-tab="analytics" onclick="switchTab('analytics')">
      Analytics
    </button>
  </div>
</div>

<!-- ── Content ───────────────────────────────────────────────── -->
<div id="content">

  <!-- ═══════════ FEEDBACK TAB ═══════════ -->
  <div class="tab-panel active" id="tab-feedback">

    <!-- KPI Row — label at TOP, then icon+number below (exact ERP Approval Dashboard layout) -->
    <div class="kpi-row">
      <div class="kpi-card">
        <div class="kpi-label">Total Feedback</div>
        <div class="kpi-body">
          <div class="kpi-icon navy"><span class="kpi-sym">&#9993;</span></div>
          <div class="kpi-nums">
            <div class="kpi-value" id="kpi-total">—</div>
            <div class="kpi-sub" id="kpi-recent">— last 7 days</div>
          </div>
        </div>
      </div>
      <div class="kpi-card">
        <div class="kpi-label">Positive Rate</div>
        <div class="kpi-body">
          <div class="kpi-icon blue" id="kpi-icon-rate"><span class="kpi-sym">&#8679;</span></div>
          <div class="kpi-nums">
            <div class="kpi-value" id="kpi-rate">—</div>
            <div class="kpi-sub" id="kpi-updown">👍 — · 👎 —</div>
          </div>
        </div>
      </div>
      <div class="kpi-card">
        <div class="kpi-label">Pending Flags</div>
        <div class="kpi-body">
          <div class="kpi-icon red" id="kpi-icon-pending"><span class="kpi-sym">!</span></div>
          <div class="kpi-nums">
            <div class="kpi-value" id="kpi-pending">—</div>
            <div class="kpi-sub">Need attention</div>
          </div>
        </div>
      </div>
      <div class="kpi-card">
        <div class="kpi-label">Resolved Flags</div>
        <div class="kpi-body">
          <div class="kpi-icon green"><span class="kpi-sym">&#10003;</span></div>
          <div class="kpi-nums">
            <div class="kpi-value success" id="kpi-resolved">—</div>
            <div class="kpi-sub" id="kpi-actionable">— actionable</div>
          </div>
        </div>
      </div>
    </div>

    <!-- Sub-tabs directly on page (not inside a card header) — matches ERP Approval Dashboard -->
    <div class="sub-tab-area">
      <div class="sub-tab-row">
        <button class="sub-tab active" data-ftab="all"      onclick="setFTab('all')">All</button>
        <button class="sub-tab"        data-ftab="pending"  onclick="setFTab('pending')">
          Pending Flag
          <span class="sub-badge" id="sub-pending-n" style="display:none"></span>
        </button>
        <button class="sub-tab"        data-ftab="resolved" onclick="setFTab('resolved')">Resolved</button>
      </div>
      <button class="btn-sm" style="margin-bottom:6px" onclick="loadStats();loadFeedback()">↻ Refresh</button>
      <button class="btn-sm danger" style="margin-bottom:6px" onclick="clearAllFeedback()">🗑 Clear All</button>
    </div>

    <!-- Content Card (filter + list only) -->
    <div class="content-card">
      <div class="content-card-body">
        <!-- Filters -->
        <div class="filter-bar">
          <select id="f-company" onchange="loadFeedback()">
            <option value="">All Companies</option>
          </select>
          <select id="f-rating" onchange="loadFeedback()">
            <option value="">All Ratings</option>
            <option value="up">👍 Thumbs Up</option>
            <option value="down">👎 Thumbs Down</option>
          </select>
          <select id="f-actionable" onchange="loadFeedback()">
            <option value="">All</option>
            <option value="1">Actionable Only</option>
          </select>
          <input type="date" id="f-from" onchange="loadFeedback()" title="From date">
          <input type="date" id="f-to"   onchange="loadFeedback()" title="To date">
          <span class="filter-spacer"></span>
          <button class="btn-sm" onclick="resetFilters()">Clear</button>
        </div>

        <!-- List -->
        <div id="fb-list" class="feedback-list">
          <div class="state-loading">Loading feedback...</div>
        </div>

        <!-- Pagination -->
        <div class="pag-row" id="fb-pag" style="display:none">
          <span class="pag-info" id="fb-pag-info"></span>
          <button class="pag-btn" id="fb-prev" onclick="changePage(-1)" disabled>← Prev</button>
          <button class="pag-btn" id="fb-next" onclick="changePage(1)">Next →</button>
        </div>
      </div>
    </div>

  </div><!-- /tab-feedback -->


  <!-- ═══════════ ACTION LOG TAB ═══════════ -->
  <div class="tab-panel" id="tab-action-log">

    <div class="content-card">
      <div class="content-card-header">
        <span class="content-card-title">Admin Action Log</span>
        <button class="btn-sm" onclick="loadActionLog()">↻ Refresh</button>
      </div>
      <div class="content-card-body">

        <div class="filter-bar">
          <select id="lg-action" onchange="loadActionLog()">
            <option value="">All Actions</option>
            <option value="resolve_flag">Resolve Flag</option>
            <option value="unflag">Unflag</option>
            <option value="manual_flag">Manual Flag</option>
            <option value="upload_document">Upload Document</option>
            <option value="run_ingest">Run Ingest</option>
            <option value="ingest_completed">Ingest Completed</option>
            <option value="ingest_failed">Ingest Failed</option>
            <option value="scheduler_enable">Scheduler Enable</option>
            <option value="scheduler_disable">Scheduler Disable</option>
            <option value="scheduler_run_now">Scheduler Run Now</option>
            <option value="clear_feedback">Clear Feedback</option>
          </select>
          <select id="lg-target" onchange="loadActionLog()">
            <option value="">All Targets</option>
            <option value="entry_version">Entry Version</option>
            <option value="document">Document</option>
            <option value="scheduler_job">Scheduler Job</option>
          </select>
          <input type="date" id="lg-from" onchange="loadActionLog()" title="From date">
          <input type="date" id="lg-to"   onchange="loadActionLog()" title="To date">
          <span class="filter-spacer"></span>
          <button class="btn-sm" onclick="resetLogFilters()">Clear</button>
        </div>

        <div class="log-wrap">
          <table class="log-tbl">
            <thead>
              <tr>
                <th>Date / Time</th>
                <th>Admin</th>
                <th>Action</th>
                <th>Target</th>
                <th>Note / Detail</th>
                <th>IP</th>
              </tr>
            </thead>
            <tbody id="lg-tbody">
              <tr><td colspan="6" class="state-loading">Loading...</td></tr>
            </tbody>
          </table>
        </div>

        <div class="pag-row" id="lg-pag" style="display:none">
          <span class="pag-info" id="lg-pag-info"></span>
          <button class="pag-btn" id="lg-prev" onclick="changeLogPage(-1)" disabled>← Prev</button>
          <button class="pag-btn" id="lg-next" onclick="changeLogPage(1)">Next →</button>
        </div>
      </div>
    </div>

  </div><!-- /tab-action-log -->


  <!-- ═══════════ DOCUMENTS TAB ═══════════ -->
  <div class="tab-panel" id="tab-documents">

    <!-- KPI Row -->
    <div class="kpi-row">
      <div class="kpi-card">
        <div class="kpi-label">Total Documents</div>
        <div class="kpi-body">
          <div class="kpi-icon navy"><span class="kpi-sym">&#128196;</span></div>
          <div class="kpi-nums">
            <div class="kpi-value" id="doc-kpi-total">—</div>
            <div class="kpi-sub" id="doc-kpi-entries">— entries extracted</div>
          </div>
        </div>
      </div>
      <div class="kpi-card">
        <div class="kpi-label">Ingested</div>
        <div class="kpi-body">
          <div class="kpi-icon green"><span class="kpi-sym">&#10003;</span></div>
          <div class="kpi-nums">
            <div class="kpi-value success" id="doc-kpi-done">—</div>
            <div class="kpi-sub">Successfully done</div>
          </div>
        </div>
      </div>
      <div class="kpi-card">
        <div class="kpi-label">Failed</div>
        <div class="kpi-body">
          <div class="kpi-icon red"><span class="kpi-sym">!</span></div>
          <div class="kpi-nums">
            <div class="kpi-value" id="doc-kpi-failed">—</div>
            <div class="kpi-sub">Ingest errors</div>
          </div>
        </div>
      </div>
      <div class="kpi-card">
        <div class="kpi-label">Queued / Running</div>
        <div class="kpi-body">
          <div class="kpi-icon blue"><span class="kpi-sym">&#8635;</span></div>
          <div class="kpi-nums">
            <div class="kpi-value" id="doc-kpi-queued">—</div>
            <div class="kpi-sub" id="doc-kpi-processing">— processing now</div>
          </div>
        </div>
      </div>
    </div>

    <!-- Content Card -->
    <div class="content-card">
      <div class="content-card-header">
        <span class="content-card-title">Document Registry</span>
        <div style="display:flex;gap:8px">
          <button class="btn-sm" style="background:var(--g3-primary);color:#fff;border-color:var(--g3-primary)" onclick="openUploadModal()">+ Upload</button>
          <button class="btn-sm" onclick="loadDocStats();loadDocuments()">↻ Refresh</button>
        </div>
      </div>
      <div class="content-card-body">

        <!-- Filters -->
        <div class="filter-bar">
          <select id="doc-status" onchange="docPage=0;loadDocuments()">
            <option value="">All Status</option>
            <option value="done">Done</option>
            <option value="failed">Failed</option>
            <option value="pending">Pending</option>
            <option value="processing">Processing</option>
          </select>
          <select id="doc-scope" onchange="docPage=0;loadDocuments()">
            <option value="">All Scope</option>
            <option value="global">Global</option>
          </select>
          <select id="doc-domain" onchange="docPage=0;loadDocuments()">
            <option value="">All Domains</option>
          </select>
          <input type="text" id="doc-search" placeholder="Search file path…"
                 oninput="clearTimeout(_docST);_docST=setTimeout(()=>{docPage=0;loadDocuments()},350)">
          <span class="filter-spacer"></span>
          <button class="btn-sm" onclick="resetDocFilters()">Clear</button>
        </div>

        <!-- Table -->
        <div class="log-wrap">
          <table class="log-tbl">
            <thead>
              <tr>
                <th style="width:32px"></th>
                <th>File</th>
                <th>Scope</th>
                <th>Domain</th>
                <th>Status</th>
                <th style="text-align:right;padding-right:20px">Entries</th>
                <th>Ingested</th>
                <th style="width:160px"></th>
              </tr>
            </thead>
            <tbody id="doc-tbody">
              <tr><td colspan="8" class="state-loading">Loading...</td></tr>
            </tbody>
          </table>
        </div>

        <!-- Pagination -->
        <div class="pag-row" id="doc-pag" style="display:none">
          <span class="pag-info" id="doc-pag-info"></span>
          <button class="pag-btn" id="doc-prev" onclick="changeDocPage(-1)" disabled>← Prev</button>
          <button class="pag-btn" id="doc-next" onclick="changeDocPage(1)">Next →</button>
        </div>
      </div>
    </div>

  </div><!-- /tab-documents -->

  <!-- Upload Document Modal -->
  <div id="upload-modal-overlay" style="display:none;position:fixed;inset:0;background:rgba(0,0,0,0.45);z-index:1000;align-items:center;justify-content:center">
    <div style="background:#fff;border-radius:10px;padding:28px 32px;width:440px;max-width:95vw;box-shadow:0 8px 32px rgba(30,58,110,0.18)">
      <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:20px">
        <h3 style="margin:0;font-size:16px;color:var(--g3-primary)">Upload Document</h3>
        <button onclick="closeUploadModal()" style="background:none;border:none;font-size:20px;cursor:pointer;color:var(--g3-text-muted);line-height:1">&times;</button>
      </div>

      <div style="margin-bottom:16px">
        <label style="display:block;font-size:12px;font-weight:600;color:var(--g3-text);margin-bottom:6px">File <span style="color:var(--g3-danger)">*</span></label>
        <div id="upload-drop-zone" onclick="document.getElementById('upload-file-input').click()"
             style="border:2px dashed var(--g3-border);border-radius:8px;padding:24px;text-align:center;cursor:pointer;transition:border-color 0.15s"
             ondragover="event.preventDefault();this.style.borderColor='var(--g3-primary)'"
             ondragleave="this.style.borderColor='var(--g3-border)'"
             ondrop="handleUploadDrop(event)">
          <div id="upload-drop-label" style="font-size:13px;color:var(--g3-text-muted)">
            &#128196; Click or drag &amp; drop .docx / .pdf here
          </div>
        </div>
        <input type="file" id="upload-file-input" accept=".docx,.pdf" style="display:none" onchange="handleUploadFileSelect(this)">
      </div>

      <div style="margin-bottom:16px">
        <label style="display:block;font-size:12px;font-weight:600;color:var(--g3-text);margin-bottom:6px">Domain <span style="color:var(--g3-danger)">*</span></label>
        <select id="upload-domain" style="width:100%;padding:8px 10px;border:1.5px solid var(--g3-border);border-radius:6px;font-size:13px" onchange="toggleDomainHint(this.value)">
          <option value="">— Select domain —</option>
          <option value="auto">🔍 Auto Detect from content</option>
          <option>Sales</option><option>Purchase</option><option>Finance</option>
          <option>Inventory</option><option>CRM</option><option>Human Resources</option>
          <option>Project</option><option>Fixed Assets</option><option>Service Manager</option>
          <option>General</option>
        </select>
        <div id="upload-domain-hint" style="display:none;font-size:11px;color:var(--g3-text-muted);margin-top:5px">
          Domain will be detected from document content using AI.
        </div>
      </div>

      <div style="margin-bottom:24px">
        <label style="display:block;font-size:12px;font-weight:600;color:var(--g3-text);margin-bottom:6px">Scope</label>
        <div style="display:flex;gap:8px;align-items:center">
          <label style="display:flex;align-items:center;gap:6px;cursor:pointer;font-size:13px">
            <input type="radio" name="upload-scope" value="" checked onchange="toggleUploadCompany(false)"> Global
          </label>
          <label style="display:flex;align-items:center;gap:6px;cursor:pointer;font-size:13px">
            <input type="radio" name="upload-scope" value="company" onchange="toggleUploadCompany(true)"> Company
          </label>
          <input type="text" id="upload-company" placeholder="e.g. ABC" maxlength="10"
                 style="display:none;padding:6px 10px;border:1.5px solid var(--g3-border);border-radius:6px;font-size:13px;width:110px;text-transform:uppercase">
        </div>
      </div>

      <div style="display:flex;justify-content:flex-end;gap:10px">
        <button class="btn-sm" onclick="closeUploadModal()">Cancel</button>
        <button id="upload-submit-btn" class="btn-sm"
                style="background:var(--g3-primary);color:#fff;border-color:var(--g3-primary);min-width:80px"
                onclick="submitUpload()">Upload</button>
      </div>
    </div>
  </div>


  <!-- ═══════════ SCHEDULER TAB ═══════════ -->
  <div class="tab-panel" id="tab-scheduler">

    <!-- KPI Row -->
    <div class="kpi-row">
      <div class="kpi-card">
        <div class="kpi-label">Document Ingest</div>
        <div class="kpi-body">
          <div class="kpi-icon navy"><span class="kpi-sym">&#128196;</span></div>
          <div class="kpi-nums">
            <div class="kpi-value" id="sched-kpi-doc-status">—</div>
            <div class="kpi-sub" id="sched-kpi-doc-sub">—</div>
          </div>
        </div>
      </div>
      <div class="kpi-card">
        <div class="kpi-label">Ticket Ingest</div>
        <div class="kpi-body">
          <div class="kpi-icon blue"><span class="kpi-sym">&#127917;</span></div>
          <div class="kpi-nums">
            <div class="kpi-value" id="sched-kpi-tkt-status">—</div>
            <div class="kpi-sub" id="sched-kpi-tkt-sub">—</div>
          </div>
        </div>
      </div>
    </div>

    <!-- Sub-tab bar -->
    <div class="sub-tab-area">
      <div class="sub-tab-row">
        <button class="sub-tab active" data-stab="jobs" onclick="setSchedTab('jobs')">Jobs</button>
        <button class="sub-tab" data-stab="log" onclick="setSchedTab('log')">Run History</button>
      </div>
      <button class="btn-sm" style="margin-bottom:6px" onclick="loadScheduler()">↻ Refresh</button>
    </div>

    <!-- Jobs panel -->
    <div id="sched-panel-jobs">
      <div class="sched-grid" id="sched-jobs-grid">
        <div class="state-loading">Loading scheduler status...</div>
      </div>
    </div>

    <!-- Run History panel -->
    <div id="sched-panel-log" style="display:none">
      <div class="content-card">
        <div class="content-card-body">
          <div class="log-wrap">
            <table class="log-tbl">
              <thead>
                <tr>
                  <th>Date / Time</th>
                  <th>Job</th>
                  <th>Triggered by</th>
                  <th>Result</th>
                  <th>Duration</th>
                  <th>Note</th>
                </tr>
              </thead>
              <tbody id="sched-log-tbody">
                <tr><td colspan="6" class="state-loading">Loading...</td></tr>
              </tbody>
            </table>
          </div>
          <div class="pag-row" id="sched-log-pag" style="display:none">
            <span class="pag-info" id="sched-log-pag-info"></span>
            <button class="pag-btn" id="sched-log-prev" onclick="changeSchedLogPage(-1)" disabled>← Prev</button>
            <button class="pag-btn" id="sched-log-next" onclick="changeSchedLogPage(1)">Next →</button>
          </div>
        </div>
      </div>
    </div>

  </div><!-- /tab-scheduler -->

  <!-- ═══════════ KNOWLEDGE BASE TAB ═══════════ -->
  <div class="tab-panel" id="tab-knowledge">

    <!-- KPI Row -->
    <div class="kpi-row">
      <div class="kpi-card">
        <div class="kpi-label">Knowledge Domains</div>
        <div class="kpi-body">
          <div class="kpi-icon navy"><span class="kpi-sym">&#127760;</span></div>
          <div class="kpi-nums">
            <div class="kpi-value" id="kb-kpi-domains">—</div>
            <div class="kpi-sub" id="kb-kpi-features">— features</div>
          </div>
        </div>
      </div>
      <div class="kpi-card">
        <div class="kpi-label">Indexed Entries</div>
        <div class="kpi-body">
          <div class="kpi-icon blue"><span class="kpi-sym">&#128196;</span></div>
          <div class="kpi-nums">
            <div class="kpi-value" id="kb-kpi-entries">—</div>
            <div class="kpi-sub" id="kb-kpi-versions">— versions total</div>
          </div>
        </div>
      </div>
      <div class="kpi-card">
        <div class="kpi-label">By Type</div>
        <div class="kpi-body">
          <div class="kpi-icon light"><span class="kpi-sym" style="font-size:22px">&#9998;</span></div>
          <div class="kpi-nums">
            <div class="kpi-sub" id="kb-kpi-types" style="font-size:13px;line-height:1.8">—</div>
          </div>
        </div>
      </div>
      <div class="kpi-card">
        <div class="kpi-label">Flagged Versions</div>
        <div class="kpi-body">
          <div class="kpi-icon red"><span class="kpi-sym">&#9873;</span></div>
          <div class="kpi-nums">
            <div class="kpi-value" id="kb-kpi-flagged">—</div>
            <div class="kpi-sub">pending review</div>
          </div>
        </div>
      </div>
    </div>

    <div style="display:flex;justify-content:flex-end;margin-bottom:12px">
      <button id="kb-delete-all-btn" class="btn-sm danger" onclick="deleteAllKbEntries()">&#128465; Delete All</button>
    </div>

    <!-- Entry list card -->
    <div class="content-card">
      <div class="content-card-header">
        <div class="content-card-title">Knowledge Entries</div>
      </div>
      <div class="content-card-body">

        <!-- Filter bar -->
        <div class="filter-bar">
          <select id="kb-f-domain" onchange="kbApply()">
            <option value="">All Domains</option>
          </select>
          <select id="kb-f-type" onchange="kbApply()">
            <option value="">All Types</option>
            <option value="procedure">Procedure</option>
            <option value="error_fix">Error Fix</option>
            <option value="faq">FAQ</option>
            <option value="reference">Reference</option>
          </select>
          <select id="kb-f-flagged" onchange="kbApply()">
            <option value="">All</option>
            <option value="1">Flagged only</option>
          </select>
          <input type="text" class="kb-search-input" id="kb-f-search"
                 placeholder="Search name / summary…"
                 onkeydown="if(event.key==='Enter') kbApply()">
          <button class="btn-sm" onclick="kbApply()">Apply</button>
          <button class="btn-sm" onclick="kbReset()">Reset</button>
          <div class="filter-spacer"></div>
          <span id="kb-count-label" style="font-size:12px;color:var(--g3-text-muted)"></span>
        </div>

        <!-- Table -->
        <div class="log-wrap">
          <table class="log-tbl">
            <thead>
              <tr>
                <th>Domain › Feature</th>
                <th>Entry Name</th>
                <th>Type</th>
                <th>Sources</th>
                <th style="text-align:center">Versions</th>
                <th style="text-align:center">Score</th>
                <th style="text-align:center">Flagged</th>
                <th style="text-align:center;width:70px">Actions</th>
              </tr>
            </thead>
            <tbody id="kb-tbody">
              <tr><td colspan="8" class="state-loading">Loading…</td></tr>
            </tbody>
          </table>
        </div>

        <div class="pag-row" id="kb-pag" style="display:none">
          <span class="pag-info" id="kb-pag-info"></span>
          <button class="pag-btn" id="kb-prev" onclick="kbChangePage(-1)" disabled>← Prev</button>
          <button class="pag-btn" id="kb-next" onclick="kbChangePage(1)">Next →</button>
        </div>

      </div>
    </div>

  </div><!-- /tab-knowledge -->

  <!-- ═══════════ HEALTH TAB ═══════════ -->
  <div class="tab-panel" id="tab-health">

    <!-- KPI Row -->
    <div class="kpi-row">
      <div class="kpi-card">
        <div class="kpi-label">Overall Status</div>
        <div class="kpi-body">
          <div class="kpi-icon green" id="h-kpi-icon-status"><span class="kpi-sym">&#10003;</span></div>
          <div class="kpi-nums">
            <div class="kpi-value success" id="h-kpi-status">—</div>
            <div class="kpi-sub" id="h-kpi-ts">Not checked</div>
          </div>
        </div>
      </div>
      <div class="kpi-card">
        <div class="kpi-label">Services Up</div>
        <div class="kpi-body">
          <div class="kpi-icon navy"><span class="kpi-sym">&#9881;</span></div>
          <div class="kpi-nums">
            <div class="kpi-value" id="h-kpi-services">—</div>
            <div class="kpi-sub">of 5 services</div>
          </div>
        </div>
      </div>
      <div class="kpi-card">
        <div class="kpi-label">Models Ready</div>
        <div class="kpi-body">
          <div class="kpi-icon blue"><span class="kpi-sym">&#11044;</span></div>
          <div class="kpi-nums">
            <div class="kpi-value" id="h-kpi-models">—</div>
            <div class="kpi-sub">of 4 configured</div>
          </div>
        </div>
      </div>
      <div class="kpi-card">
        <div class="kpi-label">Issues</div>
        <div class="kpi-body">
          <div class="kpi-icon green" id="h-kpi-icon-issues"><span class="kpi-sym">!</span></div>
          <div class="kpi-nums">
            <div class="kpi-value success" id="h-kpi-issues">—</div>
            <div class="kpi-sub">components degraded</div>
          </div>
        </div>
      </div>
    </div>

    <!-- Services -->
    <div class="content-card">
      <div class="content-card-header">
        <span class="content-card-title">Services</span>
        <span id="h-last-check" style="font-size:11px;color:var(--g3-text-muted)"></span>
        <label style="font-size:12px;display:flex;align-items:center;gap:5px;cursor:pointer;margin-left:auto">
          <input type="checkbox" id="h-auto-refresh" onchange="toggleHAutoRefresh()"> Auto 30s
        </label>
        <button class="btn-sm" style="margin-left:8px" onclick="loadHealth()">&#8635; Refresh</button>
      </div>
      <div class="content-card-body">
        <div id="h-services-grid" style="display:grid;grid-template-columns:repeat(auto-fill,minmax(175px,1fr));gap:12px">
          <div class="state-loading"></div>
        </div>
      </div>
    </div>

    <!-- Models -->
    <div class="content-card">
      <div class="content-card-header">
        <span class="content-card-title">Models</span>
      </div>
      <table class="log-tbl">
        <thead><tr><th>Role</th><th>Model Name</th><th>Status</th></tr></thead>
        <tbody id="h-models-body">
          <tr><td colspan="3" class="state-loading"></td></tr>
        </tbody>
      </table>
    </div>

    <!-- Databases -->
    <div class="content-card">
      <div class="content-card-header">
        <span class="content-card-title">Databases</span>
      </div>
      <table class="log-tbl">
        <thead><tr><th>Name</th><th>Path</th><th>Size</th><th>Records</th><th>Status</th></tr></thead>
        <tbody id="h-db-body">
          <tr><td colspan="5" class="state-loading"></td></tr>
        </tbody>
      </table>
    </div>

    <!-- Scheduler Summary -->
    <div class="content-card">
      <div class="content-card-header">
        <span class="content-card-title">Scheduler Jobs</span>
      </div>
      <table class="log-tbl">
        <thead><tr><th>Job</th><th>Enabled</th><th>Running</th><th>Last Run</th><th>Last Status</th><th>Duration</th></tr></thead>
        <tbody id="h-sched-body">
          <tr><td colspan="6" class="state-loading"></td></tr>
        </tbody>
      </table>
    </div>

  </div><!-- /tab-health -->

  <!-- ═══════════ ANALYTICS TAB (Phase 6) ═══════════ -->
  <div class="tab-panel" id="tab-analytics">

    <!-- KPI Row -->
    <div class="kpi-row">
      <div class="kpi-card">
        <div class="kpi-label">Active Users</div>
        <div class="kpi-body">
          <div class="kpi-icon navy"><span class="kpi-sym">&#128100;</span></div>
          <div class="kpi-nums">
            <div class="kpi-value" id="anl-kpi-users">—</div>
            <div class="kpi-sub"  id="anl-kpi-users-sub">in last 30 days</div>
          </div>
        </div>
      </div>
      <div class="kpi-card">
        <div class="kpi-label">Total Messages</div>
        <div class="kpi-body">
          <div class="kpi-icon blue"><span class="kpi-sym">&#128172;</span></div>
          <div class="kpi-nums">
            <div class="kpi-value" id="anl-kpi-msgs">—</div>
            <div class="kpi-sub"  id="anl-kpi-msgs-sub">user messages (stored)</div>
          </div>
        </div>
      </div>
      <div class="kpi-card">
        <div class="kpi-label">Feedback Given</div>
        <div class="kpi-body">
          <div class="kpi-icon navy"><span class="kpi-sym">&#9993;</span></div>
          <div class="kpi-nums">
            <div class="kpi-value" id="anl-kpi-fb">—</div>
            <div class="kpi-sub"  id="anl-kpi-fb-sub">ratings submitted</div>
          </div>
        </div>
      </div>
      <div class="kpi-card">
        <div class="kpi-label">Positive Rate</div>
        <div class="kpi-body">
          <div class="kpi-icon green" id="anl-kpi-icon-rate"><span class="kpi-sym">&#128077;</span></div>
          <div class="kpi-nums">
            <div class="kpi-value" id="anl-kpi-rate">—</div>
            <div class="kpi-sub">thumbs up rate</div>
          </div>
        </div>
      </div>
    </div>

    <!-- Filter Bar -->
    <div class="filter-bar" style="margin-bottom:20px">
      <select id="anl-company" onchange="anlApplyFilters()">
        <option value="">All Companies</option>
      </select>
      <select id="anl-range" onchange="anlApplyFilters()">
        <option value="7">Last 7 days</option>
        <option value="30" selected>Last 30 days</option>
        <option value="90">Last 90 days</option>
      </select>
      <button class="btn-sm" onclick="anlApplyFilters()">&#8635; Refresh</button>
    </div>

    <!-- Sub-tabs -->
    <div class="sub-tab-area">
      <div class="sub-tab-row">
        <button class="sub-tab active" data-anltab="overview"  onclick="setAnlTab('overview')">Overview</button>
        <button class="sub-tab"        data-anltab="users"     onclick="setAnlTab('users')">Users</button>
        <button class="sub-tab"        data-anltab="queries"   onclick="setAnlTab('queries')">Query Insights</button>
      </div>
    </div>

    <!-- Overview Panel -->
    <div id="anl-panel-overview">
      <p class="anl-note">Message counts are based on stored history (last 6 messages/session are retained).</p>

      <div class="anl-chart-row cols-1">
        <div class="anl-chart-wrap">
          <div class="anl-chart-title">Daily Activity</div>
          <canvas id="chart-activity"></canvas>
        </div>
      </div>

      <div class="anl-chart-row cols-2">
        <div class="anl-chart-wrap">
          <div class="anl-chart-title">Feedback Trend</div>
          <canvas id="chart-feedback"></canvas>
        </div>
        <div class="anl-chart-wrap">
          <div class="anl-chart-title">Language Preference</div>
          <canvas id="chart-language"></canvas>
        </div>
      </div>
    </div>

    <!-- Users Panel -->
    <div id="anl-panel-users" style="display:none">
      <div class="content-card">
        <div class="content-card-header">
          <span class="content-card-title">User Activity</span>
          <span id="anl-users-count" style="font-size:12px;color:var(--g3-text-muted)"></span>
        </div>
        <div class="content-card-body" style="padding:0">
          <table class="log-tbl" style="width:100%">
            <thead>
              <tr>
                <th>User</th>
                <th>Company</th>
                <th>Messages</th>
                <th>Last Seen</th>
                <th>Feedback</th>
                <th>Pos. Rate</th>
                <th>Language</th>
                <th>Resp. Len</th>
              </tr>
            </thead>
            <tbody id="anl-users-body">
              <tr><td colspan="8" class="state-msg">Loading…</td></tr>
            </tbody>
          </table>
        </div>
      </div>
      <div class="pager" id="anl-pager" style="display:none">
        <button onclick="anlUsersPage(-1)">&#8592; Prev</button>
        <span id="anl-page-info"></span>
        <button onclick="anlUsersPage(1)">Next &#8594;</button>
      </div>
    </div>

    <!-- Query Insights Panel -->
    <div id="anl-panel-queries" style="display:none">
      <div class="anl-chart-row cols-2">
        <div class="anl-chart-wrap">
          <div class="anl-chart-title">Top Domains (via Feedback)</div>
          <canvas id="chart-domains"></canvas>
        </div>
        <div class="anl-chart-wrap">
          <div class="anl-chart-title">Downvote Reasons</div>
          <canvas id="chart-reasons"></canvas>
        </div>
      </div>
      <div class="content-card">
        <div class="content-card-header">
          <span class="content-card-title">Most Frequent Queries</span>
          <span style="font-size:11px;color:var(--g3-text-muted)">from feedback submissions</span>
        </div>
        <div class="content-card-body" id="anl-queries-list">
          <p class="state-msg">Loading…</p>
        </div>
      </div>
    </div>

  </div><!-- /tab-analytics -->

</div><!-- /content -->

<!-- ── Resolve Modal ─────────────────────────────────────────── -->
<div id="modal-overlay">
  <div class="modal-box">
    <div class="modal-title">Mark Flag as Resolved</div>
    <div class="modal-sub" id="modal-entry">Entry: —</div>
    <textarea class="modal-ta" id="modal-note"
      placeholder="Describe what was done to resolve this issue (required)..."></textarea>
    <div class="modal-err" id="modal-err">Please enter a resolution note.</div>
    <div class="modal-foot">
      <button class="btn-modal-cancel" onclick="closeModal()">Cancel</button>
      <button class="btn-modal-ok" id="btn-ok" onclick="confirmResolve()">Mark Resolved</button>
    </div>
  </div>
</div>

<!-- ── Flag Modal ─────────────────────────────────────────────── -->
<div id="flag-modal-overlay" style="display:none;position:fixed;inset:0;background:rgba(30,58,110,0.22);z-index:9000;align-items:center;justify-content:center">
  <div class="modal-box">
    <div class="modal-title">🚩 Flag Entry for Review</div>
    <div class="modal-sub" id="flag-modal-entry">Entry: —</div>
    <select id="flag-reason" class="modal-ta" style="height:36px;resize:none;padding:0 10px">
      <option value="wrong_answer">Wrong answer — doesn't match question</option>
      <option value="incomplete">Incomplete — missing steps or details</option>
      <option value="outdated">Outdated — steps don't match current system</option>
      <option value="too_complex">Too complex — hard to follow</option>
      <option value="other">Other</option>
    </select>
    <textarea class="modal-ta" id="flag-note" style="margin-top:8px"
      placeholder="Additional note (optional)..."></textarea>
    <div class="modal-foot">
      <button class="btn-modal-cancel" onclick="closeFlagModal()">Cancel</button>
      <button class="btn-modal-ok" id="btn-flag-ok" style="background:var(--g3-danger)" onclick="confirmFlag()">Flag for Review</button>
    </div>
  </div>
</div>

<!-- ── Knowledge Entry Drawer ─────────────────────────────── -->
<div id="kb-drawer">
  <div id="kb-drawer-backdrop" onclick="closeKbDrawer()"></div>
  <div id="kb-drawer-panel">
    <div id="kb-drawer-head">
      <div id="kb-drawer-title">—</div>
      <button onclick="closeKbDrawer()"
              style="border:none;background:none;cursor:pointer;font-size:22px;color:var(--g3-text-muted);padding:0 4px;line-height:1;flex-shrink:0">&times;</button>
    </div>
    <div id="kb-drawer-body"></div>
  </div>
</div>

<!-- ── Toast ─────────────────────────────────────────────────── -->
<div id="toast"></div>

<script>
// ─── Config ──────────────────────────────────────────────────────────────────
<cfoutput>
const API     = "#JSStringFormat(aiApiUrl)#";
const API_KEY = "#JSStringFormat(aiApiKey)#";
</cfoutput>
const H       = { "Content-Type": "application/json", "X-API-Key": API_KEY };
const ADMIN   = "<cfoutput>#adminUserId#</cfoutput>";
const CO      = "<cfoutput>#adminCompany#</cfoutput>";
const PG      = 20;

// ─── State ───────────────────────────────────────────────────────────────────
let fbPage = 0, fbTotal = 0, fbTab = "all";
let lgPage = 0, lgTotal = 0;
let resolveId = null, resolveName = "";
let anlPage = 0, anlTotal = 0, anlTab = "overview", anlCharts = {};
let kbPage = 0, kbTotal = 0, kbDomainsLoaded = false;

// ─── Boot ────────────────────────────────────────────────────────────────────
document.getElementById("meta-user").textContent =
  ADMIN + (CO ? "  ·  " + CO : "") + "  ·  " + new Date().toLocaleDateString("en-GB", {day:"2-digit",month:"short",year:"numeric"});

loadStats();
loadFeedback();

// ─── Tab switching ────────────────────────────────────────────────────────────
function switchTab(name) {
  document.querySelectorAll(".tab-panel").forEach(p => p.classList.remove("active"));
  document.getElementById("tab-" + name).classList.add("active");
  document.querySelectorAll(".mod-tab[data-tab]").forEach(btn => {
    btn.classList.toggle("active", btn.dataset.tab === name);
  });
  if (name === "action-log") loadActionLog();
  if (name === "documents")  { loadDocStats(); loadDocuments(); }
  if (name === "scheduler")  loadScheduler();
  if (name === "knowledge")  { loadKbStats(); loadKbEntries(); }
  if (name === "health")     loadHealth();
  if (name === "analytics")  loadAnalytics();
}

// ─── Feedback sub-tab ─────────────────────────────────────────────────────────
function setFTab(t) {
  fbTab = t; fbPage = 0;
  document.querySelectorAll(".sub-tab[data-ftab]").forEach(b =>
    b.classList.toggle("active", b.dataset.ftab === t));
  loadFeedback();
}

function resetFilters() {
  ["f-company","f-rating","f-actionable","f-from","f-to"]
    .forEach(id => document.getElementById(id).value = "");
  fbPage = 0; loadFeedback();
}

function changePage(d) { fbPage = Math.max(0, fbPage + d); loadFeedback(); }

// ─── Stats ────────────────────────────────────────────────────────────────────
async function loadStats() {
  try {
    const d = await apiFetch("/admin/feedback/stats");
    const total   = d.total ?? 0;
    const up      = d.thumbs_up ?? 0;
    const down    = d.thumbs_down ?? 0;
    const rate    = d.positive_rate ?? 0;
    const pending = d.flagged_pending ?? 0;
    const resolved= d.flagged_resolved ?? 0;

    set("kpi-total",     total);
    set("kpi-recent",    "+" + (d.recent_7d ?? 0) + " last 7 days");
    set("kpi-rate",      rate + "%");
    set("kpi-updown",    "👍 " + up + "  ·  👎 " + down);
    set("kpi-pending",   pending);
    set("kpi-resolved",  resolved);
    set("kpi-actionable",(d.actionable_count ?? 0) + " actionable");

    // Pending icon stays red; value color changes by count
    document.getElementById("kpi-pending").className =
      pending > 0 ? "kpi-value danger" : "kpi-value";

    // Rate icon color + value color by rate
    const ri = document.getElementById("kpi-icon-rate");
    const rv = document.getElementById("kpi-rate");
    if (rate >= 70) {
      ri.style.background = "var(--g3-success)";
      rv.className = "kpi-value success";
    } else if (rate < 50) {
      ri.style.background = "var(--g3-danger)";
      rv.className = "kpi-value danger";
    } else {
      ri.style.background = "#2e6fd9";
      rv.className = "kpi-value";
    }

    // Sidebar + sub-tab badge
    const pBadge = document.getElementById("tab-badge-pending");
    const sBadge = document.getElementById("sub-pending-n");
    if (pending > 0) {
      pBadge.textContent = pending; pBadge.style.display = "";
      sBadge.textContent = pending; sBadge.style.display = "";
    } else {
      pBadge.style.display = "none";
      sBadge.style.display = "none";
    }
  } catch(e) { console.error("Stats:", e); }
}

// ─── Feedback list ────────────────────────────────────────────────────────────
async function loadFeedback() {
  const list = document.getElementById("fb-list");
  list.innerHTML = '<div class="state-loading">Loading feedback...</div>';

  const p = new URLSearchParams();
  const co = val("f-company"), rt = val("f-rating"),
        ac = val("f-actionable"), df = val("f-from"), dt = val("f-to");

  if (co) p.set("company_id",  co);
  if (rt) p.set("rating",      rt);
  if (ac) p.set("is_actionable", ac);
  if (df) p.set("date_from",   df);
  if (dt) p.set("date_to",     dt);
  if (fbTab !== "all") p.set("flag_status", fbTab);
  p.set("limit", PG); p.set("offset", fbPage * PG);

  try {
    const d = await apiFetch("/admin/feedback?" + p);
    fbTotal = d.total ?? 0;
    populateCos(d.items ?? []);
    renderFeedback(d.items ?? [], list);
    renderFbPag();
  } catch(e) {
    list.innerHTML = '<div class="state-msg">Failed to load. Check API connection.</div>';
  }
}

function populateCos(items) {
  const sel = document.getElementById("f-company");
  const cur = sel.value;
  const seen = new Set([...sel.options].map(o => o.value).filter(Boolean));
  items.forEach(it => {
    if (it.company_id && !seen.has(it.company_id)) {
      seen.add(it.company_id);
      const o = document.createElement("option");
      o.value = it.company_id; o.textContent = it.company_id;
      sel.appendChild(o);
    }
  });
  sel.value = cur;
}

function renderFeedback(items, container) {
  if (!items.length) {
    container.innerHTML = '<div class="state-msg">No feedback found for the selected filters.</div>';
    return;
  }
  container.innerHTML = "";
  items.forEach(item => container.appendChild(buildFbCard(item)));
}

function buildFbCard(item) {
  const isFlagged = item.is_flagged;
  const fs        = item.flag_status;
  const isDown    = item.rating === "down";
  const name      = item.entry_name || "(unknown entry)";
  const crumb     = [item.domain, item.feature].filter(Boolean).join(" › ");
  const evId      = item.entry_version_id;

  const card = document.createElement("div");
  card.className = "fb-card" +
    (isFlagged && fs !== "resolved" ? " flag-pending"  :
     isFlagged && fs === "resolved" ? " flag-resolved" : "");

  // Small badge on collapsed row
  let flagBadge = "";
  if (isFlagged && fs !== "resolved")
    flagBadge = `<span class="badge badge-pending">⚑ Pending</span>`;
  else if (isFlagged && fs === "resolved")
    flagBadge = `<span class="badge badge-resolved">✓ Resolved</span>`;

  // Resolved info (read-only, no action buttons)
  let resolvedInfo = "";
  if (isFlagged && fs === "resolved") {
    resolvedInfo = `<div class="resolved-info">
      <span>✓ Resolved</span>
      ${item.flag_resolved_by ? `<span>by <strong>${esc(item.flag_resolved_by)}</strong></span>` : ""}
      ${item.flag_resolved_at  ? `<span>· ${fmtD(item.flag_resolved_at)}</span>` : ""}
      ${item.flag_resolution_note ? `<span style="font-style:italic">· "${esc(item.flag_resolution_note)}"</span>` : ""}
    </div>`;
  }

  card.innerHTML = `
    <div class="fb-row" onclick="this.parentElement.classList.toggle('open')" title="Click to view details">
      <span class="fb-icon">${isDown ? "👎" : "👍"}</span>
      <div class="fb-main">
        <div class="fb-name">
          ${esc(name)}
          ${flagBadge}
          ${item.is_actionable ? '<span class="badge badge-action">Actionable</span>' : ""}
        </div>
        <div class="fb-crumb">${esc(crumb) || "—"}</div>
      </div>
      <div class="fb-right">
        ${item.reason ? `<span class="badge badge-reason">${fmtReason(item.reason)}</span>` : ""}
        <span style="font-size:11px;color:var(--g3-text-muted)">${fmtD(item.created_at)}</span>
        <div class="fb-row-btns">
          ${evId && isFlagged && fs !== "resolved" ? `<button class="fb-icon-btn resolve-btn" title="Mark Resolved" onclick="event.stopPropagation();openModal(${evId},'${ea(name)}')">✅</button>` : ""}
          ${evId && isFlagged && fs !== "resolved" ? `<button class="fb-icon-btn unflag-btn"  title="Unflag"         onclick="event.stopPropagation();doUnflag(${evId},'${ea(name)}')">🏳️</button>` : ""}
          ${evId && !isFlagged                     ? `<button class="fb-icon-btn flag-btn"    title="Flag for Review" onclick="event.stopPropagation();doFlag(${evId},'${ea(name)}')">🚩</button>` : ""}
          ${evId ? `<button class="fb-icon-btn" title="View Action Log" onclick="event.stopPropagation();viewLog(${evId})">📋</button>` : ""}
        </div>
        <span class="fb-chevron">▶</span>
      </div>
    </div>
    <div class="fb-detail">
      ${resolvedInfo}
      <div class="fb-grid">
        <div class="fb-field">
          <div class="fb-flabel">User</div>
          <div class="fb-fval">${esc(item.user_id || "—")}${item.company_id ? "  ·  " + esc(item.company_id) : ""}</div>
        </div>
        <div class="fb-field">
          <div class="fb-flabel">Rating</div>
          <div class="fb-fval">${isDown ? "👎 Thumbs Down" : "👍 Thumbs Up"}</div>
        </div>
        ${item.comment_normalized ? `
        <div class="fb-field span2">
          <div class="fb-flabel">Normalized Comment</div>
          <div class="fb-fval">${esc(item.comment_normalized)}</div>
        </div>` : ""}
        ${item.content_issue ? `
        <div class="fb-field span2">
          <div class="fb-flabel">Content Issue</div>
          <div class="fb-fval" style="color:var(--g3-danger)">${esc(item.content_issue)}</div>
        </div>` : ""}
        ${item.query_text ? `
        <div class="fb-field span2">
          <div class="fb-flabel">Original Query</div>
          <div class="fb-query">"${esc(item.query_text)}"</div>
        </div>` : ""}
        ${item.comment_raw ? `
        <div class="fb-field span2">
          <div class="fb-flabel">User Comment</div>
          <div class="fb-query" style="font-style:normal;color:var(--g3-text-soft)">${esc(item.comment_raw)}</div>
        </div>` : ""}
      </div>
    </div>`;
  return card;
}

function renderFbPag() {
  const el = document.getElementById("fb-pag");
  if (fbTotal <= PG) { el.style.display = "none"; return; }
  el.style.display = "";
  const tp = Math.ceil(fbTotal / PG);
  set("fb-pag-info", `Page ${fbPage+1} / ${tp}  (${fbTotal} records)`);
  document.getElementById("fb-prev").disabled = fbPage === 0;
  document.getElementById("fb-next").disabled = (fbPage+1)*PG >= fbTotal;
}

// ─── Flag actions ─────────────────────────────────────────────────────────────
function openModal(evId, name) {
  resolveId = evId; resolveName = name;
  document.getElementById("modal-entry").textContent = "Entry: " + name;
  document.getElementById("modal-note").value = "";
  document.getElementById("modal-err").style.display = "none";
  document.getElementById("modal-overlay").classList.add("open");
  setTimeout(() => document.getElementById("modal-note").focus(), 60);
}
function closeModal() {
  document.getElementById("modal-overlay").classList.remove("open");
  resolveId = null;
}
async function confirmResolve() {
  const note = document.getElementById("modal-note").value.trim();
  if (!note) { document.getElementById("modal-err").style.display = ""; return; }
  const btn = document.getElementById("btn-ok");
  btn.disabled = true; btn.textContent = "Saving...";
  try {
    await apiFetch(`/admin/entries/${resolveId}/resolve-flag`, "POST",
                   { admin_user_id: ADMIN, note });
    closeModal(); toast("Flag marked as resolved");
    loadStats(); loadFeedback();
  } catch(e) { toast("Error: " + e.message, true); }
  finally { btn.disabled = false; btn.textContent = "Mark Resolved"; }
}
async function doUnflag(evId, name) {
  if (!confirm(`Unflag "${name}"?\nThis removes the flag completely.`)) return;
  try {
    await apiFetch(`/admin/entries/${evId}/unflag`, "POST", { admin_user_id: ADMIN });
    toast("Entry unflagged"); loadStats(); loadFeedback();
  } catch(e) { toast("Error: " + e.message, true); }
}
function viewLog(evId) {
  document.getElementById("lg-action").value = "";
  document.getElementById("lg-target").value = "entry_version";
  lgPage = 0; switchTab("action-log"); loadActionLog(evId);
}

// ─── Manual flag by admin ─────────────────────────────────────────────────────
let flagEvId = null, flagEvName = "";
function doFlag(evId, name) {
  flagEvId = evId; flagEvName = name;
  document.getElementById("flag-modal-entry").textContent = "Entry: " + name;
  document.getElementById("flag-note").value = "";
  const mo = document.getElementById("flag-modal-overlay");
  mo.style.display = "flex";
  setTimeout(() => document.getElementById("flag-reason").focus(), 60);
}
function closeFlagModal() {
  document.getElementById("flag-modal-overlay").style.display = "none";
  flagEvId = null;
}
async function confirmFlag() {
  const reason = document.getElementById("flag-reason").value;
  const note   = document.getElementById("flag-note").value.trim();
  const btn    = document.getElementById("btn-flag-ok");
  btn.disabled = true; btn.textContent = "Flagging...";
  try {
    await apiFetch(`/admin/entries/${flagEvId}/flag`, "POST",
                   { admin_user_id: ADMIN, reason, note });
    closeFlagModal();
    toast("Entry flagged for review");
    loadStats(); loadFeedback();
  } catch(e) { toast("Error: " + e.message, true); }
  finally { btn.disabled = false; btn.textContent = "Flag for Review"; }
}

// ─── Clear All Feedback ───────────────────────────────────────────────────────
async function clearAllFeedback() {
  const confirmed = confirm(
    "Clear ALL feedback?\n\n" +
    "This will:\n" +
    "  • Delete all feedback log entries\n" +
    "  • Reset thumbs up/down scores on all knowledge entries\n" +
    "  • Remove all flags from entry versions\n\n" +
    "This action is intended for testing/demo only and cannot be undone."
  );
  if (!confirmed) return;

  try {
    const d = await apiFetch("/admin/feedback/all", "DELETE", { admin_user_id: ADMIN });
    toast(`Cleared ${d.deleted_count} feedback records · reset ${d.reset_count} entry versions`);
    loadStats();
    loadFeedback();
  } catch(e) {
    toast("Error: " + e.message, true);
  }
}

// ─── KB Entry Actions ─────────────────────────────────────────────────────────
async function deleteKbEntry(id, name) {
  if (!confirm(`Delete entry "${name}"?\nIt will be hidden from the knowledge base.`)) return;
  try {
    const d = await apiFetch("/admin/knowledge/entries/" + id, "DELETE", { admin_user_id: ADMIN });
    toast(`Entry "${d.name}" deleted`);
    loadKbEntries();
  } catch(e) {
    toast("Error: " + e.message, true);
  }
}

async function deleteAllKbEntries() {
  if (!confirm(
    "Delete ALL knowledge entries?\n\n" +
    "All entries will be hidden from the knowledge base.\n" +
    "You will need to run ingest to rebuild."
  )) return;
  const btn = document.getElementById("kb-delete-all-btn");
  btn.disabled = true;
  btn.textContent = "Deleting…";
  try {
    const d = await apiFetch("/admin/knowledge/entries", "DELETE", { admin_user_id: ADMIN });
    toast(d.count + " entries deleted");
    loadKbStats();
    loadKbEntries();
  } catch(e) {
    toast("Error: " + e.message, true);
  } finally {
    btn.disabled = false;
    btn.innerHTML = "&#128465; Delete All";
  }
}

// ─── Action log ───────────────────────────────────────────────────────────────
async function loadActionLog(targetId) {
  const tbody = document.getElementById("lg-tbody");
  tbody.innerHTML = '<tr><td colspan="6" class="state-loading">Loading...</td></tr>';

  const p = new URLSearchParams();
  const ac = val("lg-action"), tt = val("lg-target"),
        df = val("lg-from"),   dt = val("lg-to");
  if (ac) p.set("action",      ac);
  if (tt) p.set("target_type", tt);
  if (df) p.set("date_from",   df);
  if (dt) p.set("date_to",     dt);
  if (targetId) p.set("target_id", String(targetId));
  p.set("limit", PG); p.set("offset", lgPage * PG);

  try {
    const d = await apiFetch("/admin/action-log?" + p);
    lgTotal = d.total ?? 0;
    renderLog(d.items ?? [], tbody);
    renderLgPag();
  } catch(e) {
    tbody.innerHTML = '<tr><td colspan="6" class="state-msg">Failed to load.</td></tr>';
  }
}
function renderLog(items, tbody) {
  if (!items.length) {
    tbody.innerHTML = '<tr><td colspan="6" class="state-msg">No entries found.</td></tr>';
    return;
  }
  tbody.innerHTML = "";
  items.forEach(item => {
    const meta = item.meta ? tryJSON(item.meta) : null;
    let detail = item.note || "";
    if (meta) {
      const parts = [];
      if (meta.entry_name)        parts.push(meta.entry_name);
      if (meta.file_name)         parts.push(meta.file_name);
      if (meta.job)               parts.push("job: " + meta.job);
      if (meta.entries_parsed !== undefined) parts.push(meta.entries_parsed + " entries");
      if (meta.duration_sec)      parts.push(meta.duration_sec + "s");
      if (meta.error_snippet)     parts.push("⚠ " + meta.error_snippet);
      if (parts.length) detail = (detail ? detail + "  ·  " : "") + parts.join("  ·  ");
    }
    const tr = document.createElement("tr");
    tr.innerHTML = `
      <td style="white-space:nowrap;font-size:11px">${fmtDFull(item.created_at)}</td>
      <td style="font-weight:600">${esc(item.admin_user_id)}</td>
      <td><span class="act-badge ${esc(item.action)}">${esc(item.action)}</span></td>
      <td style="font-size:11px;color:var(--g3-text-muted)">
        ${esc(item.target_type || "")}${item.target_id ? " #" + esc(item.target_id) : ""}
      </td>
      <td style="max-width:260px">${esc(detail) || "<span style='color:var(--g3-text-muted)'>—</span>"}</td>
      <td style="font-size:11px;color:var(--g3-text-muted)">${esc(item.ip_address || "—")}</td>`;
    tbody.appendChild(tr);
  });
}
function changeLogPage(d) { lgPage = Math.max(0, lgPage + d); loadActionLog(); }
function renderLgPag() {
  const el = document.getElementById("lg-pag");
  if (lgTotal <= PG) { el.style.display = "none"; return; }
  el.style.display = "";
  const tp = Math.ceil(lgTotal / PG);
  set("lg-pag-info", `Page ${lgPage+1} / ${tp}  (${lgTotal} records)`);
  document.getElementById("lg-prev").disabled = lgPage === 0;
  document.getElementById("lg-next").disabled = (lgPage+1)*PG >= lgTotal;
}
function resetLogFilters() {
  ["lg-action","lg-target","lg-from","lg-to"].forEach(id => document.getElementById(id).value = "");
  lgPage = 0; loadActionLog();
}

// ─── Utilities ────────────────────────────────────────────────────────────────
async function apiFetch(path, method, body) {
  const opts = { method: method || "GET", headers: H };
  if (body) opts.body = JSON.stringify(body);
  const res = await fetch(API + path, opts);
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}

function fmtReason(r) {
  if (!r) return "";
  return r.split("_").map(w => w.charAt(0).toUpperCase() + w.slice(1)).join(" ");
}

function esc(s) {
  if (!s && s !== 0) return "";
  return String(s).replace(/&/g,"&amp;").replace(/</g,"&lt;")
                  .replace(/>/g,"&gt;").replace(/"/g,"&quot;");
}
function ea(s) { return String(s||"").replace(/'/g,"\\'"); }
function val(id) { return document.getElementById(id).value; }
function set(id, v) { const el = document.getElementById(id); if (el) el.textContent = v; }
function tryJSON(s) { try { return JSON.parse(s); } catch { return null; } }

function fmtD(iso) {
  if (!iso) return "—";
  const d = new Date(iso); if (isNaN(d)) return iso;
  const today = new Date();
  if (d.toDateString() === today.toDateString())
    return d.toLocaleTimeString("en-GB",{hour:"2-digit",minute:"2-digit"});
  return d.toLocaleDateString("en-GB",{day:"2-digit",month:"short"}) + " " +
         d.toLocaleTimeString("en-GB",{hour:"2-digit",minute:"2-digit"});
}
function fmtDFull(iso) {
  if (!iso) return "—";
  const d = new Date(iso); if (isNaN(d)) return iso;
  return d.toLocaleDateString("en-GB",{day:"2-digit",month:"short",year:"numeric"}) +
         " " + d.toLocaleTimeString("en-GB",{hour:"2-digit",minute:"2-digit"});
}

let _toastT;
function toast(msg, err) {
  const t = document.getElementById("toast");
  t.textContent = msg;
  t.className = "show" + (err ? " error" : "");
  clearTimeout(_toastT);
  _toastT = setTimeout(() => t.className = "", 2800);
}

// ─── Documents ────────────────────────────────────────────────────────────────
let docPage = 0, docTotal = 0, _docST = null;
let _docPollTimer = null, _docItems = [];

function _checkDocPolling() {
  const hasProcessing = _docItems.some(d => d.status === 'processing');
  if (hasProcessing && !_docPollTimer) {
    _docPollTimer = setInterval(() => { loadDocStats(); loadDocuments(true); }, 3000);
  } else if (!hasProcessing && _docPollTimer) {
    clearInterval(_docPollTimer);
    _docPollTimer = null;
  }
}

async function loadDocStats() {
  try {
    const d = await apiFetch("/admin/documents/stats");
    const failed  = d.failed  ?? 0;
    const queued  = (d.pending ?? 0) + (d.processing ?? 0);
    set("doc-kpi-total",      d.total ?? 0);
    set("doc-kpi-entries",    (d.total_entries ?? 0).toLocaleString() + " entries extracted");
    set("doc-kpi-done",       d.done ?? 0);
    set("doc-kpi-failed",     failed);
    set("doc-kpi-queued",     queued);
    set("doc-kpi-processing", (d.processing ?? 0) + " processing now");
    document.getElementById("doc-kpi-failed").className =
      failed > 0 ? "kpi-value danger" : "kpi-value";
  } catch(e) { console.error("DocStats:", e); }
}

async function loadDocuments(silent = false) {
  const tbody = document.getElementById("doc-tbody");
  if (!silent) tbody.innerHTML = '<tr><td colspan="8" class="state-loading">Loading...</td></tr>';

  const p = new URLSearchParams();
  const st = val("doc-status"), sc = val("doc-scope"),
        dm = val("doc-domain"), q  = document.getElementById("doc-search").value.trim();
  if (st) p.set("status",     st);
  if (sc) p.set("company_id", sc);
  if (dm) p.set("domain",     dm);
  if (q)  p.set("search",     q);
  p.set("limit", PG); p.set("offset", docPage * PG);

  try {
    const d = await apiFetch("/admin/documents?" + p);
    docTotal = d.total ?? 0;
    _docItems = d.items ?? [];
    populateDocFilters(_docItems);
    renderDocTable(_docItems, tbody);
    renderDocPag();
    _checkDocPolling();
  } catch(e) {
    if (!silent)
      tbody.innerHTML = '<tr><td colspan="8" class="state-msg">Failed to load. Check API connection.</td></tr>';
  }
}

function populateDocFilters(items) {
  const cSel = document.getElementById("doc-scope");
  const cSeen = new Set([...cSel.options].map(o => o.value).filter(Boolean));
  items.forEach(it => {
    if (it.company_code && !cSeen.has(it.company_code)) {
      cSeen.add(it.company_code);
      const o = document.createElement("option");
      o.value = it.company_code;
      o.textContent = it.company_code + (it.company_name ? " — " + it.company_name : "");
      cSel.appendChild(o);
    }
  });
  const dSel = document.getElementById("doc-domain");
  const dSeen = new Set([...dSel.options].map(o => o.value).filter(Boolean));
  items.forEach(it => {
    if (it.domain_name && !dSeen.has(it.domain_name)) {
      dSeen.add(it.domain_name);
      const o = document.createElement("option");
      o.value = it.domain_name; o.textContent = it.domain_name;
      dSel.appendChild(o);
    }
  });
}

function renderDocTable(items, tbody) {
  if (!items.length) {
    tbody.innerHTML = '<tr><td colspan="8" class="state-msg">No documents found.</td></tr>';
    return;
  }
  tbody.innerHTML = "";
  items.forEach(item => {
    const rawPath = (item.file_path || "").replace(/\\/g, "/");
    const docsMatch = rawPath.match(/documents\/(.+)/);
    const relPath = docsMatch ? docsMatch[1] : rawPath;
    const parts  = relPath.split("/");
    const fname  = parts[parts.length - 1] || rawPath;
    const fdir   = parts.slice(0, -1).join(" / ");
    const scope  = item.company_code || "Global";
    const isFail = item.status === "failed";

    const tr = document.createElement("tr");
    tr.title = item.file_path || "";
    if (isFail && item.error_message) {
      tr.style.cursor = "pointer";
      tr.onclick = () => {
        const next = tr.nextSibling;
        if (next && next.classList.contains("doc-err-row"))
          next.style.display = next.style.display === "none" ? "" : "none";
      };
    }
    tr.innerHTML = `
      <td style="text-align:center;font-size:14px;padding-left:14px">${docIcon(item.file_path)}</td>
      <td>
        <div style="font-size:12px;font-weight:600;color:var(--g3-text)">${esc(fname)}</div>
        ${fdir ? `<div style="font-size:10px;color:var(--g3-text-muted);margin-top:2px">${esc(fdir)}</div>` : ""}
      </td>
      <td style="font-size:11px;color:var(--g3-text-muted)">${esc(scope)}</td>
      <td style="font-size:11px;color:var(--g3-text-muted)">${esc(item.domain_name || "—")}</td>
      <td>
        <span class="doc-status ${esc(item.status)}">${esc(item.status)}</span>
        ${item.status === 'processing' ? '<div class="doc-progress-wrap"><div class="doc-progress-bar"></div></div>' : ''}
      </td>
      <td style="font-size:12px;text-align:right;padding-right:20px">${item.entries_parsed ?? 0}</td>
      <td style="font-size:11px;white-space:nowrap;color:var(--g3-text-muted)">${fmtD(item.ingested_at || item.created_at)}</td>
      <td style="text-align:right;padding-right:12px">
        <div style="display:flex;gap:4px;justify-content:flex-end;flex-wrap:wrap">
          ${item.status === "failed" || item.status === "done"
            ? `<button class="btn-sm" style="font-size:11px;height:26px;padding:0 8px"
                 onclick="event.stopPropagation();queueReingest(${item.id},'${ea(fname)}',this)">Re-ingest</button>`
            : `<span style="font-size:11px;color:var(--g3-text-muted);line-height:26px">${item.status === "pending" ? "Queued" : item.status === "processing" ? "Running…" : ""}</span>`
          }
          ${item.status === "pending" || item.status === "failed"
            ? `<button class="btn-sm" style="font-size:11px;height:26px;padding:0 8px;background:var(--g3-primary);color:#fff;border-color:var(--g3-primary)"
                 onclick="event.stopPropagation();runNowDoc(${item.id},'${ea(fname)}',this)">▶ Now</button>`
            : ""
          }
          <button class="btn-sm" style="font-size:11px;height:26px;padding:0 8px;color:var(--g3-danger);border-color:var(--g3-danger)"
                  onclick="event.stopPropagation();deleteDoc(${item.id},'${ea(fname)}',this)">✕</button>
        </div>
      </td>`;
    tbody.appendChild(tr);

    if (isFail && item.error_message) {
      const errRow = document.createElement("tr");
      errRow.className = "doc-err-row";
      errRow.style.display = "none";
      errRow.innerHTML = `<td colspan="8"><div class="doc-err-snippet">${esc(item.error_message)}</div></td>`;
      tbody.appendChild(errRow);
    }
  });
}

function docIcon(path) {
  if (!path) return "📄";
  const ext = path.split(".").pop().toLowerCase();
  if (ext === "pdf")  return "📕";
  if (ext === "docx" || ext === "doc") return "📘";
  return "📄";
}

async function queueReingest(docId, fname, btn) {
  if (!confirm(`Queue "${fname}" for re-ingest?\n\nStatus will reset to pending — the scheduler will pick it up on the next run.`)) return;
  btn.disabled = true; btn.textContent = "Queuing…";
  try {
    await apiFetch(`/admin/documents/${docId}/reingest`, "POST", { admin_user_id: ADMIN, note: "" });
    toast("Queued for re-ingest");
    loadDocStats(); loadDocuments();
  } catch(e) { toast("Error: " + e.message, true); }
  finally { btn.disabled = false; btn.textContent = "Re-ingest"; }
}

// ─── Upload modal ─────────────────────────────────────────────────────────────
let _uploadFile = null;

function openUploadModal() {
  _uploadFile = null;
  document.getElementById("upload-file-input").value = "";
  document.getElementById("upload-drop-label").innerHTML = "&#128196; Click or drag &amp; drop .docx / .pdf here";
  document.getElementById("upload-drop-zone").style.borderColor = "var(--g3-border)";
  document.getElementById("upload-domain").value = "";
  document.getElementById("upload-domain-hint").style.display = "none";
  document.querySelectorAll("input[name='upload-scope']")[0].checked = true;
  toggleUploadCompany(false);
  document.getElementById("upload-submit-btn").disabled = false;
  document.getElementById("upload-submit-btn").textContent = "Upload";
  const ov = document.getElementById("upload-modal-overlay");
  ov.style.display = "flex";
}

function closeUploadModal() {
  document.getElementById("upload-modal-overlay").style.display = "none";
}

function toggleUploadCompany(show) {
  document.getElementById("upload-company").style.display = show ? "inline-block" : "none";
  if (!show) document.getElementById("upload-company").value = "";
}

function toggleDomainHint(val) {
  document.getElementById("upload-domain-hint").style.display = val === "auto" ? "block" : "none";
}

function handleUploadFileSelect(input) {
  if (input.files[0]) _setUploadFile(input.files[0]);
}

function handleUploadDrop(ev) {
  ev.preventDefault();
  document.getElementById("upload-drop-zone").style.borderColor = "var(--g3-border)";
  const f = ev.dataTransfer.files[0];
  if (f) _setUploadFile(f);
}

function _setUploadFile(f) {
  const ext = f.name.split(".").pop().toLowerCase();
  if (ext !== "docx" && ext !== "pdf") { toast("Only .docx and .pdf files are supported", true); return; }
  _uploadFile = f;
  document.getElementById("upload-drop-label").innerHTML =
    `&#128196; <strong>${esc(f.name)}</strong> (${(f.size/1024).toFixed(1)} KB)`;
  document.getElementById("upload-drop-zone").style.borderColor = "var(--g3-primary)";
}

async function submitUpload() {
  if (!_uploadFile) { toast("Please select a file", true); return; }
  const domain = document.getElementById("upload-domain").value;
  if (!domain) { toast("Please select a domain", true); return; }
  const scopeIsCompany = document.querySelector("input[name='upload-scope']:checked").value === "company";
  const company = scopeIsCompany ? document.getElementById("upload-company").value.trim().toUpperCase() : "";
  if (scopeIsCompany && !company) { toast("Please enter a company code", true); return; }

  const btn = document.getElementById("upload-submit-btn");
  btn.disabled = true; btn.textContent = "Uploading…";

  const fd = new FormData();
  fd.append("file", _uploadFile);
  fd.append("domain", domain);
  fd.append("company_code", company);
  fd.append("admin_user_id", ADMIN);

  try {
    const res = await fetch(API + "/admin/documents/upload", {
      method: "POST",
      headers: { "X-API-Key": API_KEY },
      body: fd,
    });
    if (!res.ok) throw new Error(await res.text());
    const d = await res.json();
    const domainLabel = d.auto_detected ? ` · domain: ${d.domain}` : "";
    toast(`Uploaded: ${_uploadFile.name}${domainLabel} — status: ${d.status}`);
    closeUploadModal();
    loadDocStats(); loadDocuments();
  } catch(e) {
    toast("Upload failed: " + e.message, true);
    btn.disabled = false; btn.textContent = "Upload";
  }
}

// ─── Delete document ──────────────────────────────────────────────────────────
async function deleteDoc(docId, fname, btn) {
  if (!confirm(`Delete "${fname}"?\n\nThis will remove the file from disk and the registry. This cannot be undone.`)) return;
  btn.disabled = true;
  try {
    await apiFetch(`/admin/documents/${docId}?admin_user_id=${encodeURIComponent(ADMIN)}`, "DELETE", null);
    toast(`Deleted: ${fname}`);
    loadDocStats(); loadDocuments();
  } catch(e) {
    toast("Delete failed: " + e.message, true);
    btn.disabled = false;
  }
}

// ─── Run ingest immediately ───────────────────────────────────────────────────
async function runNowDoc(docId, fname, btn) {
  if (!confirm(`Run ingest now for "${fname}"?\n\nThis will process the file immediately in the background.`)) return;
  btn.disabled = true; btn.textContent = "Starting…";
  try {
    await apiFetch(`/admin/documents/${docId}/run-now`, "POST", { admin_user_id: ADMIN, note: "" });
    toast("Ingest started — status will update automatically");
    loadDocStats(); loadDocuments();
  } catch(e) {
    toast("Error: " + e.message, true);
    btn.disabled = false; btn.textContent = "▶ Now";
  }
}

function changeDocPage(d) { docPage = Math.max(0, docPage + d); loadDocuments(); }

function renderDocPag() {
  const el = document.getElementById("doc-pag");
  if (docTotal <= PG) { el.style.display = "none"; return; }
  el.style.display = "";
  const tp = Math.ceil(docTotal / PG);
  set("doc-pag-info", `Page ${docPage+1} / ${tp}  (${docTotal} records)`);
  document.getElementById("doc-prev").disabled = docPage === 0;
  document.getElementById("doc-next").disabled = (docPage+1)*PG >= docTotal;
}

function resetDocFilters() {
  ["doc-status","doc-scope","doc-domain"].forEach(id => document.getElementById(id).value = "");
  document.getElementById("doc-search").value = "";
  docPage = 0; loadDocuments();
}

// ─── Modal close handlers ─────────────────────────────────────────────────────
document.getElementById("modal-overlay").addEventListener("click", e => {
  if (e.target === e.currentTarget) closeModal();
});
document.addEventListener("keydown", e => { if (e.key === "Escape") closeModal(); });

// ─── Scheduler ────────────────────────────────────────────────────────────────
let schedState = null;
let schedLogPage = 0, schedLogTotal = 0;

const JOB_LABELS = { documents: "Document Ingest", tickets: "Ticket Ingest" };

function setSchedTab(t) {
  document.querySelectorAll(".sub-tab[data-stab]").forEach(b =>
    b.classList.toggle("active", b.dataset.stab === t));
  document.getElementById("sched-panel-jobs").style.display = t === "jobs" ? "" : "none";
  document.getElementById("sched-panel-log").style.display  = t === "log"  ? "" : "none";
  if (t === "log") loadSchedLog();
}

async function loadScheduler() {
  try {
    schedState = await apiFetch("/admin/scheduler/status");
    renderSchedKpis(schedState);
    renderSchedJobs(schedState);
  } catch(e) {
    document.getElementById("sched-jobs-grid").innerHTML =
      '<div class="state-msg">Failed to load scheduler status. Check API connection.</div>';
  }
}

function renderSchedKpis(state) {
  const doc = state.documents || {};
  const tkt = state.tickets   || {};

  function kpiVal(job) {
    if (job.is_running) return "Running…";
    if (!job.enabled)   return "Disabled";
    return job.last_run_status === "success" ? "OK"
         : job.last_run_status === "failed"  ? "Failed"
         : "Idle";
  }
  function kpiSub(job) {
    if (job.is_running) return "In progress…";
    if (!job.last_run_at) return "Never run";
    const d = new Date(job.last_run_at);
    const dur = job.last_run_duration_sec ? " · " + job.last_run_duration_sec + "s" : "";
    return fmtD(job.last_run_at) + dur;
  }

  set("sched-kpi-doc-status", kpiVal(doc));
  set("sched-kpi-doc-sub",    kpiSub(doc));
  set("sched-kpi-tkt-status", kpiVal(tkt));
  set("sched-kpi-tkt-sub",    kpiSub(tkt));

  document.getElementById("sched-kpi-doc-status").className =
    doc.is_running ? "kpi-value" : doc.last_run_status === "failed" ? "kpi-value danger"
    : doc.last_run_status === "success" ? "kpi-value success" : "kpi-value";
  document.getElementById("sched-kpi-tkt-status").className =
    tkt.is_running ? "kpi-value" : tkt.last_run_status === "failed" ? "kpi-value danger"
    : tkt.last_run_status === "success" ? "kpi-value success" : "kpi-value";
}

function renderSchedJobs(state) {
  const grid = document.getElementById("sched-jobs-grid");
  grid.innerHTML = "";
  ["documents", "tickets"].forEach(job => {
    grid.appendChild(buildJobCard(job, state[job] || {}));
  });
}

function buildJobCard(job, cfg) {
  const isRunning  = cfg.is_running;
  const isEnabled  = cfg.enabled !== false;
  const label      = JOB_LABELS[job] || job;
  const interval   = cfg.interval || "daily";
  const runTime    = cfg.time     || "—";
  const day        = cfg.day      || "monday";

  const schedDesc = interval === "hourly" ? "Every hour"
                  : interval === "weekly" ? `Every ${cap(day)} at ${runTime}`
                  : `Daily at ${runTime}`;

  const lastRunClass = cfg.last_run_status === "success" ? "success"
                     : cfg.last_run_status === "failed"  ? "failed"
                     : cfg.is_running ? "running" : "muted";
  const lastRunText  = isRunning ? "Running now…"
                     : cfg.last_run_status ? cap(cfg.last_run_status) + (cfg.last_run_duration_sec ? ` · ${cfg.last_run_duration_sec}s` : "")
                     : "Never run";
  const lastRunAt    = cfg.last_run_at ? fmtDFull(cfg.last_run_at) : "—";

  const badgeClass = isRunning ? "running" : isEnabled ? "enabled" : "disabled";
  const dotClass   = isRunning ? "pulse"   : isEnabled ? "green"   : "gray";
  const badgeText  = isRunning ? "Running" : isEnabled ? "Enabled" : "Disabled";

  const card = document.createElement("div");
  card.className = "job-card";
  card.id = `job-card-${job}`;
  card.innerHTML = `
    <div class="job-card-header">
      <span class="job-title">${esc(label)}</span>
      <span class="job-badge ${badgeClass}" id="job-badge-${job}">
        <span class="job-dot ${dotClass}" id="job-dot-${job}"></span>
        <span id="job-badge-text-${job}">${badgeText}</span>
      </span>
    </div>
    <div class="job-body">
      <div class="job-meta-row">
        <div class="job-meta-item">
          <div class="job-meta-label">Schedule</div>
          <div class="job-meta-val" id="job-sched-${job}">${esc(schedDesc)}</div>
        </div>
        <div class="job-meta-item">
          <div class="job-meta-label">Last Run</div>
          <div class="job-meta-val ${lastRunClass}" id="job-lastrun-${job}">${esc(lastRunText)}</div>
        </div>
        <div class="job-meta-item">
          <div class="job-meta-label">At</div>
          <div class="job-meta-val muted" id="job-lastat-${job}">${esc(lastRunAt)}</div>
        </div>
      </div>

      <!-- Inline schedule edit form -->
      <div class="sched-edit-form" id="sched-form-${job}">
        <div class="sched-edit-row">
          <label>Interval</label>
          <select id="sched-interval-${job}" onchange="toggleDayField('${job}')">
            <option value="hourly"  ${interval==='hourly'  ? 'selected':''}>Hourly</option>
            <option value="daily"   ${interval==='daily'   ? 'selected':''}>Daily</option>
            <option value="weekly"  ${interval==='weekly'  ? 'selected':''}>Weekly</option>
          </select>
          <label>Time</label>
          <input type="time" id="sched-time-${job}" value="${esc(runTime)}">
          <span id="sched-day-wrap-${job}" style="${interval==='weekly'?'':'display:none'}">
            <label>Day</label>
            <select id="sched-day-${job}">
              ${["monday","tuesday","wednesday","thursday","friday","saturday","sunday"]
                .map(d => `<option value="${d}" ${day===d?'selected':''}>${cap(d)}</option>`).join("")}
            </select>
          </span>
          <button class="btn-sm primary" style="height:30px;padding:0 12px"
                  onclick="saveSchedConfig('${job}', this)">Save</button>
          <button class="btn-sm" style="height:30px;padding:0 12px"
                  onclick="toggleSchedForm('${job}')">Cancel</button>
        </div>
      </div>

      <div class="job-actions">
        <button class="btn-sm primary" id="job-runnow-${job}"
                onclick="schedRunNow('${job}', this)"
                ${isRunning ? 'disabled' : ''}>
          ${isRunning ? 'Running…' : '▶ Run Now'}
        </button>
        <button class="btn-sm" onclick="toggleSchedForm('${job}')">Edit Schedule</button>
        ${isEnabled
          ? `<button class="btn-sm" style="color:var(--g3-danger);border-color:var(--g3-danger)"
                     onclick="schedDisable('${job}', this)">Disable</button>`
          : `<button class="btn-sm" style="color:var(--g3-success);border-color:var(--g3-success)"
                     onclick="schedEnable('${job}', this)">Enable</button>`
        }
      </div>
    </div>`;
  return card;
}

function cap(s) { return s ? s.charAt(0).toUpperCase() + s.slice(1) : s; }

function toggleSchedForm(job) {
  const form = document.getElementById("sched-form-" + job);
  form.classList.toggle("open");
}

function toggleDayField(job) {
  const interval = document.getElementById("sched-interval-" + job).value;
  document.getElementById("sched-day-wrap-" + job).style.display =
    interval === "weekly" ? "" : "none";
}

async function saveSchedConfig(job, btn) {
  const interval = document.getElementById("sched-interval-" + job).value;
  const time     = document.getElementById("sched-time-" + job).value;
  const day      = document.getElementById("sched-day-" + job) ?
                   document.getElementById("sched-day-" + job).value : "monday";
  btn.disabled = true; btn.textContent = "Saving…";
  try {
    await apiFetch(`/admin/scheduler/jobs/${job}/config`, "PUT",
                   { admin_user_id: ADMIN, interval, time, day });
    toast("Schedule updated");
    toggleSchedForm(job);
    loadScheduler();
  } catch(e) { toast("Error: " + e.message, true); }
  finally { btn.disabled = false; btn.textContent = "Save"; }
}

async function schedRunNow(job, btn) {
  btn.disabled = true; btn.textContent = "Starting…";
  try {
    await apiFetch(`/admin/scheduler/jobs/${job}/run-now`, "POST",
                   { admin_user_id: ADMIN });
    toast("Job started — check Run History for results");
    setTimeout(loadScheduler, 1000);
  } catch(e) {
    const msg = e.message.includes("409") ? "Job is already running" : e.message;
    toast("Error: " + msg, true);
    btn.disabled = false; btn.textContent = "▶ Run Now";
  }
}

async function schedEnable(job, btn) {
  btn.disabled = true;
  try {
    await apiFetch(`/admin/scheduler/jobs/${job}/enable`, "POST",
                   { admin_user_id: ADMIN });
    toast("Job enabled"); loadScheduler();
  } catch(e) { toast("Error: " + e.message, true); btn.disabled = false; }
}

async function schedDisable(job, btn) {
  if (!confirm(`Disable "${JOB_LABELS[job]}"?\n\nThe scheduler daemon will skip this job on its next run.`)) return;
  btn.disabled = true;
  try {
    await apiFetch(`/admin/scheduler/jobs/${job}/disable`, "POST",
                   { admin_user_id: ADMIN });
    toast("Job disabled"); loadScheduler();
  } catch(e) { toast("Error: " + e.message, true); btn.disabled = false; }
}

// ─── Scheduler Run History (reuses action-log endpoint filtered to scheduler_job) ─
async function loadSchedLog() {
  const tbody = document.getElementById("sched-log-tbody");
  tbody.innerHTML = '<tr><td colspan="6" class="state-loading">Loading...</td></tr>';
  const p = new URLSearchParams();
  p.set("target_type", "scheduler_job");
  p.set("limit", PG); p.set("offset", schedLogPage * PG);
  try {
    const d = await apiFetch("/admin/action-log?" + p);
    schedLogTotal = d.total ?? 0;
    renderSchedLog(d.items ?? [], tbody);
    renderSchedLogPag();
  } catch(e) {
    tbody.innerHTML = '<tr><td colspan="6" class="state-msg">Failed to load.</td></tr>';
  }
}

function renderSchedLog(items, tbody) {
  if (!items.length) {
    tbody.innerHTML = '<tr><td colspan="6" class="state-msg">No scheduler history found.</td></tr>';
    return;
  }
  tbody.innerHTML = "";
  items.forEach(item => {
    const meta    = item.meta ? tryJSON(item.meta) : null;
    const dur     = meta && meta.duration_sec ? meta.duration_sec + "s" : "—";
    const trigger = meta && meta.trigger ? meta.trigger : item.admin_user_id;
    const result  = item.action === "ingest_completed" ? '<span class="badge badge-resolved">Success</span>'
                  : item.action === "ingest_failed"    ? '<span class="badge badge-pending">Failed</span>'
                  : `<span class="act-badge ${esc(item.action)}">${esc(item.action)}</span>`;
    const tr = document.createElement("tr");
    tr.innerHTML = `
      <td style="white-space:nowrap;font-size:11px">${fmtDFull(item.created_at)}</td>
      <td style="font-weight:600">${esc(JOB_LABELS[item.target_id] || item.target_id || "—")}</td>
      <td style="font-size:11px;color:var(--g3-text-muted)">${esc(trigger)}</td>
      <td>${result}</td>
      <td style="font-size:11px;color:var(--g3-text-muted)">${esc(dur)}</td>
      <td style="font-size:11px;max-width:200px;color:var(--g3-text-muted)">${esc(item.note || "")}</td>`;
    tbody.appendChild(tr);
  });
}

function changeSchedLogPage(d) { schedLogPage = Math.max(0, schedLogPage + d); loadSchedLog(); }

function renderSchedLogPag() {
  const el = document.getElementById("sched-log-pag");
  if (schedLogTotal <= PG) { el.style.display = "none"; return; }
  el.style.display = "";
  const tp = Math.ceil(schedLogTotal / PG);
  set("sched-log-pag-info", `Page ${schedLogPage+1} / ${tp}  (${schedLogTotal} records)`);
  document.getElementById("sched-log-prev").disabled = schedLogPage === 0;
  document.getElementById("sched-log-next").disabled = (schedLogPage+1)*PG >= schedLogTotal;
}

// ─── Knowledge Base Browser ────────────────────────────────────────────────────

async function loadKbStats() {
  try {
    const d = await apiFetch("/admin/knowledge/stats");
    set("kb-kpi-domains",  d.domains  ?? 0);
    set("kb-kpi-features", (d.features ?? 0) + " features");
    set("kb-kpi-entries",  d.entries  ?? 0);
    set("kb-kpi-versions", (d.versions ?? 0) + " versions total");
    const ft = d.by_type || {};
    document.getElementById("kb-kpi-types").innerHTML =
      `Procedure: ${ft.procedure||0} &nbsp;·&nbsp; Error Fix: ${ft.error_fix||0}<br>` +
      `FAQ: ${ft.faq||0} &nbsp;·&nbsp; Reference: ${ft.reference||0}`;
    const fl = d.flagged ?? 0;
    set("kb-kpi-flagged", fl);
    document.getElementById("kb-kpi-flagged").className =
      fl > 0 ? "kpi-value danger" : "kpi-value";
  } catch(e) { /* silent */ }
}

const KB_TYPE_BADGE = {
  procedure: "badge-reason",
  error_fix: "badge-pending",
  faq:       "badge-up",
  reference: "badge-action",
};
const KB_SRC_BADGE = {
  document:  "badge-resolved",
  ticket:    "badge-reason",
  augmented: "badge-action",
  manual:    "badge-up",
};

async function loadKbEntries() {
  const tbody = document.getElementById("kb-tbody");
  tbody.innerHTML = '<tr><td colspan="8" class="state-loading">Loading…</td></tr>';
  const p = new URLSearchParams();
  const domain  = document.getElementById("kb-f-domain").value;
  const type    = document.getElementById("kb-f-type").value;
  const flagged = document.getElementById("kb-f-flagged").value;
  const search  = document.getElementById("kb-f-search").value.trim();
  if (domain)  p.set("domain",      domain);
  if (type)    p.set("entry_type",  type);
  if (flagged) p.set("flagged",     flagged);
  if (search)  p.set("search",      search);
  p.set("limit",  PG);
  p.set("offset", kbPage * PG);
  try {
    const d = await apiFetch("/admin/knowledge/entries?" + p);
    kbTotal = d.total ?? 0;
    set("kb-count-label", kbTotal + " entries found");
    if (!kbDomainsLoaded && d.domains && d.domains.length) {
      const sel = document.getElementById("kb-f-domain");
      d.domains.forEach(name => {
        const opt = document.createElement("option");
        opt.value = name; opt.textContent = name;
        sel.appendChild(opt);
      });
      kbDomainsLoaded = true;
    }
    renderKbEntries(d.items ?? [], tbody);
    renderKbPag();
  } catch(e) {
    tbody.innerHTML = '<tr><td colspan="8" class="state-msg">Failed to load.</td></tr>';
  }
}

function renderKbEntries(items, tbody) {
  if (!items.length) {
    tbody.innerHTML = '<tr><td colspan="8" class="state-msg">No entries found.</td></tr>';
    return;
  }
  tbody.innerHTML = "";
  items.forEach(item => {
    const typeBadge = `<span class="badge ${KB_TYPE_BADGE[item.type]||'badge-action'}">${esc(item.type.replace("_"," "))}</span>`;
    const sources   = (item.source_types||[]).map(s =>
      `<span class="badge ${KB_SRC_BADGE[s]||'badge-action'}">${esc(s)}</span>`
    ).join(" ");
    const flagCell  = item.flagged_count > 0
      ? `<span class="badge badge-pending">&#9873; ${item.flagged_count}</span>` : "—";
    const score     = item.score != null
      ? `<span style="color:${item.score>=70?"var(--g3-success)":item.score>=40?"#b35c00":"var(--g3-danger)"};font-weight:600">${item.score}%</span>`
      : `<span style="color:var(--g3-text-muted)">—</span>`;
    const domFeat   = `<div style="font-weight:600;color:var(--g3-primary);font-size:12px">${esc(item.domain)}</div>
                       <div style="font-size:11px;color:var(--g3-text-muted);margin-top:1px">${esc(item.feature)}</div>`;
    const entryName = `<div style="font-weight:500">${esc(item.name)}</div>`
      + (item.summary
          ? `<div style="font-size:11px;color:var(--g3-text-muted);margin-top:2px">${esc(item.summary.slice(0,90))}${item.summary.length>90?"…":""}</div>`
          : "");
    const tr = document.createElement("tr");
    tr.style.cursor = "pointer";
    tr.title = "Click to view entry detail";
    tr.onclick = () => openKbDetail(item.id, item.name);
    tr.innerHTML = `
      <td>${domFeat}</td>
      <td>${entryName}</td>
      <td>${typeBadge}</td>
      <td>${sources || "—"}</td>
      <td style="text-align:center;font-weight:600">${item.version_count}</td>
      <td style="text-align:center">${score}</td>
      <td style="text-align:center">${flagCell}</td>
      <td style="text-align:center"><button class="btn-sm danger kb-del-btn" title="Delete entry" style="padding:2px 8px;font-size:12px">&#128465;</button></td>`;
    tbody.appendChild(tr);
    tr.querySelector('.kb-del-btn').addEventListener('click', e => {
      e.stopPropagation();
      deleteKbEntry(item.id, item.name);
    });
  });
}

function kbApply()  { kbPage = 0; loadKbEntries(); }
function kbReset()  {
  ["kb-f-type","kb-f-flagged"].forEach(id => document.getElementById(id).value = "");
  document.getElementById("kb-f-domain").value = "";
  document.getElementById("kb-f-search").value = "";
  kbPage = 0; loadKbEntries();
}
function kbChangePage(d) { kbPage = Math.max(0, kbPage + d); loadKbEntries(); }
function renderKbPag() {
  const el = document.getElementById("kb-pag");
  if (kbTotal <= PG) { el.style.display = "none"; return; }
  el.style.display = "";
  const tp = Math.ceil(kbTotal / PG);
  set("kb-pag-info", `Page ${kbPage+1} / ${tp}  (${kbTotal} entries)`);
  document.getElementById("kb-prev").disabled = kbPage === 0;
  document.getElementById("kb-next").disabled = (kbPage+1)*PG >= kbTotal;
}

// ─── Entry Detail Drawer ───────────────────────────────────────────────────────

async function openKbDetail(id, name) {
  const body = document.getElementById("kb-drawer-body");
  document.getElementById("kb-drawer-title").textContent = name;
  body.innerHTML = '<div class="state-loading" style="padding:40px">Loading…</div>';
  document.getElementById("kb-drawer").classList.add("open");
  try {
    const d = await apiFetch("/admin/knowledge/entries/" + id);
    renderKbDetail(d, body);
  } catch(e) {
    body.innerHTML = '<div class="state-msg">Failed to load entry.</div>';
  }
}

function closeKbDrawer() {
  document.getElementById("kb-drawer").classList.remove("open");
}

function renderKbDetail(d, body) {
  const typeBadge = `<span class="badge ${KB_TYPE_BADGE[d.type]||'badge-action'}">${esc(d.type.replace("_"," "))}</span>`;
  let html = `<div style="margin-bottom:16px;padding-bottom:16px;border-bottom:1px solid var(--g3-border)">
    <div style="margin-bottom:6px">${typeBadge}</div>
    <div style="font-size:12px;color:var(--g3-text-muted);margin-bottom:2px">
      <strong>${esc(d.domain)}</strong> &rsaquo; ${esc(d.feature)}
    </div>
    ${d.menu_path ? `<div style="font-size:11px;color:var(--g3-text-muted);font-style:italic;margin-top:4px">&#128194; ${esc(d.menu_path)}</div>` : ""}
    ${d.summary   ? `<div style="margin-top:8px;font-size:13px;line-height:1.5">${esc(d.summary)}</div>` : ""}
  </div>`;

  if (!d.versions || !d.versions.length) {
    html += '<div class="state-msg">No versions found.</div>';
    body.innerHTML = html;
    return;
  }

  d.versions.forEach(v => {
    const company  = v.company_code === "global"
      ? '<span class="badge badge-resolved">&#127760; Global</span>'
      : `<span class="badge badge-reason">&#127970; ${esc(v.company_code)}</span>`;
    const srcBadge = `<span class="badge ${KB_SRC_BADGE[v.source_type]||''}">${esc(v.source_type)}</span>`;
    const flagHtml = v.is_flagged
      ? `<span class="badge badge-pending">&#9873; ${esc(v.flag_reason || "flagged")}</span>` : "";
    const score    = v.score != null
      ? `<span style="font-size:11px;color:var(--g3-text-muted)">Score: <strong style="color:${v.score>=70?"var(--g3-success)":v.score>=40?"#b35c00":"var(--g3-danger)"}">${v.score}%</strong></span>` : "";
    const votes    = `<span style="font-size:11px;color:var(--g3-text-muted)">&#128077;${v.thumbs_up} &#128078;${v.thumbs_down}</span>`;

    html += `<div style="border:1px solid var(--g3-border);border-radius:6px;padding:14px;margin-bottom:12px">
      <div style="display:flex;align-items:center;gap:6px;margin-bottom:12px;flex-wrap:wrap">
        ${company} ${srcBadge} ${flagHtml}
        <span style="margin-left:auto"></span>${votes} ${score}
      </div>`;

    if (v.steps && v.steps.length) {
      html += `<div style="font-size:11px;font-weight:700;text-transform:uppercase;letter-spacing:.05em;color:var(--g3-text-muted);margin-bottom:6px">Steps</div>
        <ol style="margin:0 0 12px 18px;padding:0;font-size:13px;line-height:1.6">`;
      v.steps.forEach(step => {
        const text = typeof step === "string" ? step
          : (step.text || step.description || step.action || JSON.stringify(step));
        html += `<li style="margin-bottom:4px">${esc(text)}</li>`;
      });
      html += `</ol>`;
    }

    if (v.notes && v.notes.length) {
      html += `<div style="font-size:11px;font-weight:700;text-transform:uppercase;letter-spacing:.05em;color:var(--g3-text-muted);margin-bottom:6px">Notes</div>
        <ul style="margin:0 0 0 18px;padding:0;font-size:13px;line-height:1.6">`;
      v.notes.forEach(note => {
        const text = typeof note === "string" ? note : JSON.stringify(note);
        html += `<li style="margin-bottom:4px">${esc(text)}</li>`;
      });
      html += `</ul>`;
    }

    if (!v.steps?.length && !v.notes?.length) {
      html += `<div style="font-size:12px;color:var(--g3-text-muted);font-style:italic">No structured content available.</div>`;
    }

    if (v.source_ref) {
      html += `<div style="margin-top:10px;font-size:11px;color:var(--g3-text-muted)">&#128279; ${esc(v.source_ref)}</div>`;
    }
    if (v.flag_resolution_note) {
      html += `<div style="margin-top:8px;padding:8px;background:#e6f4ea;border-radius:4px;font-size:11px;color:#2d7a3a">
        <strong>Resolution:</strong> ${esc(v.flag_resolution_note)}</div>`;
    }
    html += `</div>`;
  });

  body.innerHTML = html;
}

// ─── Health Monitor ───────────────────────────────────────────────────────────

let hAutoTimer = null;

function toggleHAutoRefresh() {
  const on = document.getElementById("h-auto-refresh").checked;
  clearInterval(hAutoTimer);
  if (on) hAutoTimer = setInterval(loadHealth, 30000);
}

const H_SVC_LABELS = {
  api: "API Server", gemini: "Gemini API", chromadb: "ChromaDB",
  postgres: "PostgreSQL", skills_server: "Skills Server"
};
const H_SVC_ICONS = {
  api: "&#9670;", gemini: "&#10024;", chromadb: "&#128190;",
  postgres: "&#128208;", skills_server: "&#9881;"
};

async function loadHealth() {
  try {
    const d = await apiFetch("/admin/health");

    // Timestamp
    const cat = (d.checked_at || "").replace("T", " ").replace("Z", " UTC");
    document.getElementById("h-last-check").textContent = cat ? "Checked: " + cat : "";
    document.getElementById("h-kpi-ts").textContent     = cat || "—";

    // Counts
    const svcs    = Object.values(d.services || {});
    const svcOk   = svcs.filter(s => s.status === "ok").length;
    const mods    = d.models || [];
    const modOk   = mods.filter(m => m.available === true).length;
    const modKnown = mods.filter(m => m.available !== null).length;
    const issues  = svcs.filter(s => s.status === "down").length
                  + mods.filter(m => m.available === false).length;

    // KPI values
    document.getElementById("h-kpi-services").textContent = svcOk + " / " + svcs.length;
    document.getElementById("h-kpi-models").textContent   = modOk + " / " + modKnown;
    document.getElementById("h-kpi-issues").textContent   = issues;

    // KPI colors
    const issueIcon = document.getElementById("h-kpi-icon-issues");
    const issueVal  = document.getElementById("h-kpi-issues");
    issueIcon.className = issues === 0 ? "kpi-icon green" : "kpi-icon red";
    issueVal.className  = issues === 0 ? "kpi-value success" : "kpi-value danger";

    const stIcon = document.getElementById("h-kpi-icon-status");
    const stVal  = document.getElementById("h-kpi-status");
    if (issues === 0) {
      stIcon.className  = "kpi-icon green";
      stVal.textContent = "Healthy";
      stVal.className   = "kpi-value success";
    } else {
      stIcon.className  = "kpi-icon red";
      stVal.textContent = "Issues";
      stVal.className   = "kpi-value danger";
    }

    // Services grid
    let sg = "";
    for (const [key, svc] of Object.entries(d.services || {})) {
      const isOk   = svc.status === "ok";
      const isSkip = svc.status === "skip";
      const dot    = `<span style="width:8px;height:8px;border-radius:50%;background:${isOk?"#34a853":isSkip?"#8a9bb5":"#e53935"};flex-shrink:0;display:inline-block"></span>`;
      const badge  = isOk ? "badge-resolved" : isSkip ? "" : "badge-pending";
      const ms     = svc.response_ms != null ? `<div style="font-size:10px;color:var(--g3-text-muted);margin-top:4px">${svc.response_ms} ms</div>` : "";
      const extra  = svc.model_count != null ? `<div style="font-size:10px;color:var(--g3-text-muted)">${svc.model_count} models</div>` : "";
      sg += `<div style="border:1px solid var(--g3-border);border-radius:6px;padding:12px">
        <div style="display:flex;align-items:center;gap:6px;margin-bottom:6px">${dot}
          <span style="font-size:12px;font-weight:700">${H_SVC_LABELS[key]||key}</span>
        </div>
        <span class="badge ${badge}" style="align-self:flex-start">${svc.status.toUpperCase()}</span>
        ${ms}${extra}
      </div>`;
    }
    document.getElementById("h-services-grid").innerHTML = sg || '<div class="state-msg">No service data</div>';

    // Models table
    let mh = "";
    for (const m of mods) {
      const av = m.available === true
        ? '<span class="badge badge-resolved">&#10003; Ready</span>'
        : m.available === false
          ? '<span class="badge badge-pending">&#9888; Missing</span>'
          : '<span class="badge" style="background:#f5f5f5;color:#8a9bb5">&#8212; N/A</span>';
      mh += `<tr><td><strong>${esc(m.role)}</strong></td><td style="font-family:monospace;font-size:11px">${esc(m.name)}</td><td>${av}</td></tr>`;
    }
    document.getElementById("h-models-body").innerHTML =
      mh || '<tr><td colspan="3" class="state-msg">No model data</td></tr>';

    // Databases table
    const DB_LABELS = { knowledge: "Knowledge DB", chat_history: "Chat History" };
    let dh = "";
    for (const [key, db] of Object.entries(d.databases || {})) {
      const st = db.exists
        ? '<span class="badge badge-resolved">&#10003; OK</span>'
        : '<span class="badge badge-pending">&#9888; Missing</span>';
      const size = db.size_mb != null ? db.size_mb + " MB" : "—";
      let recs = "—";
      if (db.entries  != null) recs = db.entries + (db.flagged ? ` entries (${db.flagged} flagged)` : " entries");
      if (db.messages != null) recs = db.messages + " messages";
      const shortPath = (db.path || "").replace(/\\/g, "/").split("/").slice(-3).join("/");
      dh += `<tr>
        <td><strong>${DB_LABELS[key]||key}</strong></td>
        <td><span style="font-family:monospace;font-size:10px;color:var(--g3-text-muted)" title="${esc(db.path||'')}">${esc(shortPath)}</span></td>
        <td>${size}</td><td>${recs}</td><td>${st}</td>
      </tr>`;
    }
    document.getElementById("h-db-body").innerHTML =
      dh || '<tr><td colspan="5" class="state-msg">No database data</td></tr>';

    // Scheduler table
    const SC_LABELS = { documents: "Document Ingest", tickets: "Ticket Ingest" };
    let sh = "";
    for (const [job, s] of Object.entries(d.scheduler || {})) {
      const en  = s.enabled
        ? '<span class="badge badge-resolved">Enabled</span>'
        : '<span class="badge" style="background:#f5f5f5;color:#8a9bb5">Disabled</span>';
      const run = s.is_running
        ? '<span class="badge badge-action">Running</span>'
        : '<span style="color:var(--g3-text-muted)">—</span>';
      const lst = s.last_run_status === "success"
        ? '<span class="badge badge-resolved">Success</span>'
        : s.last_run_status === "failed"
          ? '<span class="badge badge-pending">Failed</span>'
          : '<span style="color:var(--g3-text-muted)">—</span>';
      const at  = s.last_run_at ? s.last_run_at.replace("T"," ").slice(0,16) : "—";
      const dur = s.last_run_duration_sec != null ? s.last_run_duration_sec + "s" : "—";
      sh += `<tr>
        <td><strong>${SC_LABELS[job]||job}</strong></td>
        <td>${en}</td><td>${run}</td>
        <td style="font-size:11px;color:var(--g3-text-muted)">${at}</td>
        <td>${lst}</td>
        <td style="font-size:12px">${dur}</td>
      </tr>`;
    }
    document.getElementById("h-sched-body").innerHTML =
      sh || '<tr><td colspan="6" class="state-msg">Scheduler state not available</td></tr>';

  } catch (e) {
    console.error("Health check failed", e);
    showToast("Health check failed: " + e.message, true);
  }
}

// ═══════════════════════════════════════════════════════════════════════════
// PHASE 6 — User Analytics
// ═══════════════════════════════════════════════════════════════════════════

const ANL_NAVY   = ['#1e3a6e','#2c5282','#4a7fc1','#8fafd8','#c5d5ec','#dde6f5'];
const ANL_GRID   = 'rgba(208,217,234,0.5)';

function anlGetRange()   { return parseInt(document.getElementById("anl-range").value, 10) || 30; }
function anlGetCompany() { return document.getElementById("anl-company").value; }

function anlRangeLabel() {
  const d = anlGetRange();
  return d === 7 ? "last 7 days" : d === 90 ? "last 90 days" : "last 30 days";
}

// Destroy and (re)create a Chart.js instance on a canvas
function renderChart(id, config) {
  if (anlCharts[id]) { anlCharts[id].destroy(); delete anlCharts[id]; }
  const ctx = document.getElementById(id);
  if (!ctx) return;
  anlCharts[id] = new Chart(ctx, config);
}

function setAnlTab(tab) {
  anlTab = tab;
  document.querySelectorAll(".sub-tab[data-anltab]").forEach(b =>
    b.classList.toggle("active", b.dataset.anltab === tab));
  document.getElementById("anl-panel-overview").style.display = tab === "overview" ? "" : "none";
  document.getElementById("anl-panel-users").style.display    = tab === "users"    ? "" : "none";
  document.getElementById("anl-panel-queries").style.display  = tab === "queries"  ? "" : "none";
  if (tab === "users")   loadAnlUsers(true);
  if (tab === "queries") loadAnlTopQueries();
}

function anlApplyFilters() {
  anlPage = 0;
  loadAnalytics();
}

async function loadAnalytics() {
  // Populate company dropdown once
  try {
    const ov = await apiFetch(`/admin/analytics/overview?days=${anlGetRange()}`);
    _renderAnlOverview(ov);
    _populateAnlCompanies(ov.companies || []);
  } catch(e) { console.error("Analytics overview failed", e); }

  // Charts — run in background, only visible in Overview sub-tab
  loadAnlMessages();
  loadAnlFeedbackTrend();

  if (anlTab === "users")   loadAnlUsers(true);
  if (anlTab === "queries") loadAnlTopQueries();
}

function _populateAnlCompanies(companies) {
  const sel = document.getElementById("anl-company");
  const cur = sel.value;
  // Keep "All Companies" option, replace rest
  while (sel.options.length > 1) sel.remove(1);
  companies.forEach(c => {
    if (c.code && c.code !== "—") {
      const opt = new Option(c.code, c.code);
      sel.appendChild(opt);
    }
  });
  sel.value = cur;
}

function _renderAnlOverview(d) {
  const days = anlGetRange();
  set("anl-kpi-users",     d.active_users ?? 0);
  set("anl-kpi-users-sub", `in ${anlRangeLabel()}`);
  set("anl-kpi-msgs",      d.total_messages ?? 0);
  set("anl-kpi-msgs-sub",  `user messages · ${anlRangeLabel()}`);
  set("anl-kpi-fb",        d.feedback_given ?? 0);
  set("anl-kpi-fb-sub",    `ratings · ${anlRangeLabel()}`);

  const rate = d.positive_rate ?? 0;
  set("anl-kpi-rate", rate + "%");
  const rateIcon = document.getElementById("anl-kpi-icon-rate");
  const rateVal  = document.getElementById("anl-kpi-rate");
  if (rate >= 70) {
    rateIcon.className = "kpi-icon green";
    rateVal.className  = "kpi-value success";
  } else if (rate < 50 && d.feedback_given > 0) {
    rateIcon.className = "kpi-icon red";
    rateVal.className  = "kpi-value danger";
  } else {
    rateIcon.className = "kpi-icon navy";
    rateVal.className  = "kpi-value";
  }

  // Language pie
  const lang = d.language_dist || {};
  const langLabels = Object.keys(lang).map(k => k === "auto" ? "Auto" : k.toUpperCase());
  const langData   = Object.values(lang);
  renderChart("chart-language", {
    type: "doughnut",
    data: {
      labels: langLabels.length ? langLabels : ["No data"],
      datasets: [{ data: langData.length ? langData : [1], backgroundColor: ANL_NAVY,
                   borderColor: "#fff", borderWidth: 2 }]
    },
    options: {
      responsive: true, maintainAspectRatio: true,
      plugins: { legend: { position: "bottom", labels: { font: { size: 11 }, boxWidth: 12 } } }
    }
  });
}

async function loadAnlMessages() {
  try {
    const days = anlGetRange() <= 7 ? 7 : anlGetRange() <= 30 ? 14 : 30;
    const co   = anlGetCompany();
    const url  = `/admin/analytics/messages?days=${days}` + (co ? `&company_id=${co}` : "");
    const d    = await apiFetch(url);
    renderChart("chart-activity", {
      type: "line",
      data: {
        labels: d.labels || [],
        datasets: [
          {
            label: "Messages", data: d.messages || [],
            borderColor: "#1e3a6e", backgroundColor: "rgba(30,58,110,0.08)",
            borderWidth: 2, pointRadius: 3, fill: true, tension: 0.3, yAxisID: "yMsg"
          },
          {
            label: "Active Users", data: d.users || [],
            borderColor: "#4a7fc1", backgroundColor: "transparent",
            borderWidth: 2, pointRadius: 3, borderDash: [4,3], tension: 0.3, yAxisID: "yUsr"
          }
        ]
      },
      options: {
        responsive: true, maintainAspectRatio: true, interaction: { mode: "index" },
        scales: {
          yMsg: { position: "left",  beginAtZero: true, ticks: { stepSize: 1, font: { size: 10 } },
                  grid: { color: ANL_GRID } },
          yUsr: { position: "right", beginAtZero: true, ticks: { stepSize: 1, font: { size: 10 } },
                  grid: { display: false } },
          x:    { ticks: { font: { size: 10 } }, grid: { color: ANL_GRID } }
        },
        plugins: { legend: { labels: { font: { size: 11 }, boxWidth: 12 } } }
      }
    });
  } catch(e) { console.error("Messages chart failed", e); }
}

async function loadAnlFeedbackTrend() {
  try {
    const co  = anlGetCompany();
    const url = `/admin/analytics/feedback-trend?days=${anlGetRange()}` + (co ? `&company_id=${co}` : "");
    const d   = await apiFetch(url);
    renderChart("chart-feedback", {
      type: "bar",
      data: {
        labels: d.labels || [],
        datasets: [
          { label: "Thumbs Up",   data: d.thumbs_up   || [], backgroundColor: "rgba(52,168,83,0.8)",
            borderRadius: 3 },
          { label: "Thumbs Down", data: d.thumbs_down || [], backgroundColor: "rgba(229,57,53,0.8)",
            borderRadius: 3 }
        ]
      },
      options: {
        responsive: true, maintainAspectRatio: true,
        scales: {
          x: { stacked: true, ticks: { font: { size: 10 } }, grid: { color: ANL_GRID } },
          y: { stacked: true, beginAtZero: true, ticks: { stepSize: 1, font: { size: 10 } },
               grid: { color: ANL_GRID } }
        },
        plugins: { legend: { labels: { font: { size: 11 }, boxWidth: 12 } } }
      }
    });
  } catch(e) { console.error("Feedback trend chart failed", e); }
}

async function loadAnlTopQueries() {
  try {
    const co  = anlGetCompany();
    const url = `/admin/analytics/top-queries?days=${anlGetRange()}` + (co ? `&company_id=${co}` : "");
    const d   = await apiFetch(url);

    // Domains horizontal bar
    const doms = d.domains || [];
    renderChart("chart-domains", doms.length ? {
      type: "bar",
      data: {
        labels: doms.map(x => x.name),
        datasets: [{ label: "Feedback count", data: doms.map(x => x.count),
                     backgroundColor: ANL_NAVY.slice(0, doms.length), borderRadius: 4 }]
      },
      options: {
        indexAxis: "y", responsive: true, maintainAspectRatio: true,
        scales: {
          x: { beginAtZero: true, ticks: { stepSize: 1, font: { size: 10 } }, grid: { color: ANL_GRID } },
          y: { ticks: { font: { size: 11 } }, grid: { display: false } }
        },
        plugins: { legend: { display: false } }
      }
    } : {
      type: "bar", data: { labels: ["No data"], datasets: [{ data: [0] }] },
      options: { plugins: { legend: { display: false } } }
    });

    // Downvote reasons doughnut
    const reasons = d.reasons || [];
    const REASON_LABELS = { wrong_answer: "Wrong Answer", incomplete: "Incomplete",
                             outdated: "Outdated", too_complex: "Too Complex",
                             missing_images: "Missing Images", other: "Other" };
    renderChart("chart-reasons", reasons.length ? {
      type: "doughnut",
      data: {
        labels: reasons.map(r => REASON_LABELS[r.reason] || r.reason),
        datasets: [{ data: reasons.map(r => r.count),
                     backgroundColor: ANL_NAVY.slice(0, reasons.length),
                     borderColor: "#fff", borderWidth: 2 }]
      },
      options: {
        responsive: true, maintainAspectRatio: true,
        plugins: { legend: { position: "bottom", labels: { font: { size: 11 }, boxWidth: 12 } } }
      }
    } : {
      type: "doughnut",
      data: { labels: ["No downvotes"], datasets: [{ data: [1], backgroundColor: ["#e8edf8"],
              borderColor: "#fff", borderWidth: 2 }] },
      options: { plugins: { legend: { display: false } } }
    });

    // Sample queries list
    const queries  = d.queries || [];
    const listEl   = document.getElementById("anl-queries-list");
    if (!queries.length) {
      listEl.innerHTML = '<p class="state-msg">No query data yet — queries appear here after users submit feedback.</p>';
    } else {
      listEl.innerHTML =
        '<ol class="anl-query-list">' +
        queries.map(q =>
          `<li>${escHtml(q.text)}<span class="anl-query-count">×${q.count}</span></li>`
        ).join("") +
        '</ol>';
    }
  } catch(e) { console.error("Top queries failed", e); }
}

async function loadAnlUsers(reset) {
  if (reset) anlPage = 0;
  try {
    const co  = anlGetCompany();
    const url = `/admin/analytics/users?days=${anlGetRange()}&limit=${PG}&offset=${anlPage * PG}`
              + (co ? `&company_id=${co}` : "");
    const d   = await apiFetch(url);
    anlTotal  = d.total || 0;
    set("anl-users-count", anlTotal + " users");

    const RATE_BADGE = r =>
      r === null ? '<span style="color:var(--g3-text-muted)">—</span>'
      : r >= 70  ? `<span class="badge badge-ok">${r}%</span>`
      : r < 50   ? `<span class="badge badge-pending">${r}%</span>`
      :             `<span class="badge" style="background:var(--g3-primary);color:#fff">${r}%</span>`;

    const body = document.getElementById("anl-users-body");
    if (!d.items || !d.items.length) {
      body.innerHTML = `<tr><td colspan="8" class="state-msg">No user activity in ${anlRangeLabel()}.</td></tr>`;
      document.getElementById("anl-pager").style.display = "none";
      return;
    }
    body.innerHTML = d.items.map(u => `<tr>
      <td style="font-size:12px">${escHtml(u.user_id)}</td>
      <td><span class="badge" style="background:var(--g3-primary-light);color:var(--g3-primary)">${escHtml(u.company_id||"—")}</span></td>
      <td style="text-align:right">${u.messages}</td>
      <td style="font-size:11px;color:var(--g3-text-muted)">${(u.last_seen||"").replace("T"," ").slice(0,16)}</td>
      <td style="text-align:right">${u.feedback_count}</td>
      <td>${RATE_BADGE(u.positive_rate)}</td>
      <td>${(u.language||"auto").toUpperCase()}</td>
      <td style="text-transform:capitalize">${u.response_len||"normal"}</td>
    </tr>`).join("");

    const pages = Math.ceil(anlTotal / PG);
    const pager = document.getElementById("anl-pager");
    if (pages > 1) {
      pager.style.display = "";
      set("anl-page-info", `Page ${anlPage + 1} of ${pages} (${anlTotal} users)`);
      pager.querySelector("button:first-child").disabled = anlPage === 0;
      pager.querySelector("button:last-child").disabled  = anlPage >= pages - 1;
    } else {
      pager.style.display = "none";
    }
  } catch(e) { console.error("Users load failed", e); }
}

function anlUsersPage(dir) {
  anlPage = Math.max(0, anlPage + dir);
  loadAnlUsers(false);
}

function escHtml(s) {
  return String(s||"").replace(/&/g,"&amp;").replace(/</g,"&lt;").replace(/>/g,"&gt;");
}
</script>
</body>
</html>
