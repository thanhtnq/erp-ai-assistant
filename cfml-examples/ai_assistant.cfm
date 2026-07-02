<!---@ ###########################################################################################################
Version 5.0.1
File Description:
No	Modified Date	Modified By		Change Log
1.	20240701	Lopper		Creation Of File 
################################################################################################################# @--->

<cfparam name="cookie.cookuserloginid" default="m8">
<cfparam name="cookie.cookmfnunique"   default="demo2011mfn">
<cfparam name="cookie.cookcfnunique"   default="p11011004464072155">
<cfparam name="cookie.cooklang"        default="english">
<!--- aiApiUrl / aiApiKey đã chuyển sang ai_proxy.cfm, chỉ tồn tại ở server, không còn khai báo/tồn tại ở đây nữa --->
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>ERP AI Assistant</title>
  <style>
    :root {
      --av: 28px; --av-gap: 8px;
      --clr-primary:       #1e3a6e;
      --clr-primary-dark:  #142c57;
      --clr-primary-light: #e8edf8;
      --clr-bg-page:       #eaeff7;
      --clr-bg-bot:        #f0f4fb;
      --clr-bg-panel:      #f5f8fd;
      --clr-text-main:     #1e3a6e;
      --clr-text-light:    #8a9bb5;
      --clr-border:        #d0d9ea;
    }

    * { box-sizing: border-box; margin: 0; padding: 0; font-family: 'Century Gothic', CenturyGothic, AppleGothic, sans-serif; }
    html, body { height: 100%; overflow: hidden; background: var(--clr-bg-page); }

    #chat-container {
      display: flex; flex-direction: column; height: 100vh;
      background: white; position: relative;
    }

    #messages {
      flex: 1; overflow-y: auto;
      display: flex; flex-direction: column;
      scroll-behavior: smooth;
      scrollbar-width: thin;
      scrollbar-gutter: stable;
    }


    .date-sep {
      text-align: center; font-size: 11px; color: var(--clr-text-light);
      margin: 6px 0; position: relative; user-select: none;
    }
    .date-sep::before, .date-sep::after {
      content: ""; position: absolute; top: 50%; width: 25%; height: 1px; background: var(--clr-border);
    }
    .date-sep::before { left: 0; } .date-sep::after { right: 0; }

    .history-label {
      text-align: center; font-size: 11px; color: var(--clr-text-light); padding: 3px 12px;
      background: var(--clr-bg-panel); border-radius: 12px; align-self: center; margin-bottom: 2px; user-select: none;
    }

    .msg-row { display: flex; flex-direction: column; max-width: min(88%, 560px); }
    .msg-row.user { align-self: flex-end; align-items: flex-end; }
    .msg-row.bot  { align-self: flex-start; align-items: flex-start; }

    .msg-inner { display: flex; gap: var(--av-gap); align-items: flex-end; width: 100%; }
    .msg-row.user .msg-inner { flex-direction: row-reverse; }

    .bot-avatar, .user-avatar {
      width: var(--av); height: var(--av); border-radius: 50%; flex-shrink: 0;
      display: flex; align-items: center; justify-content: center;
      font-size: 12px; font-weight: 600; overflow: hidden;
    }
    .bot-avatar  { background: none; }
    .bot-avatar img { width: 100%; height: 100%; object-fit: contain; border-radius: 6px; display: block; }
    .user-avatar { background: var(--clr-primary-light); color: var(--clr-primary); }
    .user-avatar img { width: 100%; height: 100%; object-fit: cover; border-radius: 50%; }

    .bubble {
      padding: 9px 13px; border-radius: 18px;
      font-size: 13px; line-height: 1.65; word-break: break-word;
    }
    .msg-row.user .bubble { background: var(--clr-primary); color: white; border-bottom-right-radius: 4px; }
    .msg-row.bot  .bubble { background: var(--clr-bg-bot); color: var(--clr-text-main); border-bottom-left-radius: 4px; border: 1px solid var(--clr-border); }

    .msg-time {
      font-size: 10px; color: var(--clr-text-light); margin-top: 3px;
      opacity: 0; transition: opacity 0.2s; user-select: none; line-height: 1;
    }
    .msg-row.bot  .msg-time { padding-left: calc(var(--av) + var(--av-gap)); }
    .msg-row.user .msg-time { padding-right: calc(var(--av) + var(--av-gap)); }
    .msg-row:hover .msg-time { opacity: 1; }

    .response-intro { margin-bottom: 8px; line-height: 1.65; }
    .step-block { margin: 5px 0; }
    .step-text  { line-height: 1.65; }
    .suggestions {
      display: flex; flex-wrap: wrap; gap: 6px; margin-top: 10px;
      padding-top: 8px; border-top: 1px solid var(--clr-border);
    }
    .suggestion-btn {
      max-width: 100%; border: 1px solid var(--clr-border); background: white;
      color: var(--clr-text-main); border-radius: 16px; padding: 6px 10px;
      font-size: 12px; line-height: 1.35; cursor: pointer; text-align: left;
      white-space: normal; overflow-wrap: anywhere; transition: all 0.15s;
    }
    .suggestion-btn:hover {
      background: var(--clr-primary-light); border-color: var(--clr-primary);
      color: var(--clr-primary);
    }
    .chart-actions {
      margin-top: 6px; margin-left: calc(var(--av) + var(--av-gap));
      display: flex; flex-direction: column; gap: 7px; max-width: min(88%, 560px);
    }
    .chart-question {
      font-size: 12px; color: var(--clr-text-main); background: var(--clr-bg-panel);
      border: 1px solid var(--clr-border); border-radius: 14px; padding: 7px 10px;
    }
    .chart-option-row { display: flex; flex-wrap: wrap; gap: 6px; }
    .chart-toggle {
      border: 1px solid var(--clr-border); background: white; color: var(--clr-primary);
      border-radius: 16px; padding: 6px 10px; font-size: 12px; cursor: pointer;
    }
    .chart-toggle.active { background: var(--clr-primary); border-color: var(--clr-primary); color: white; }
    .chart-toggle:hover { background: var(--clr-primary-light); border-color: var(--clr-primary); }
    .chart-toggle.active:hover { background: var(--clr-primary-dark); color: white; }
    .rank-chart {
      margin-top: 8px; padding: 8px; border: 1px solid var(--clr-border);
      border-radius: 8px; background: white; display: flex; flex-direction: column; gap: 7px;
    }
    .rank-chart svg { width: 100%; height: 190px; display: block; overflow: visible; }
    .rank-chart-empty { font-size: 12px; color: var(--clr-text-light); }
    .rank-chart-row {
      display: grid; grid-template-columns: minmax(96px, 42%) 1fr auto;
      gap: 7px; align-items: center; min-height: 18px;
    }
    .rank-chart-label {
      font-size: 11px; color: var(--clr-text-main); overflow: hidden;
      text-overflow: ellipsis; white-space: nowrap;
    }
    .rank-chart-track {
      height: 8px; border-radius: 999px; background: var(--clr-primary-light); overflow: hidden;
    }
    .rank-chart-bar { height: 100%; border-radius: inherit; background: var(--clr-primary); min-width: 2px; }
    .rank-chart-value { font-size: 11px; color: var(--clr-text-light); white-space: nowrap; }

    .tw-cursor {
      display: inline-block; width: 2px; height: 13px;
      background: var(--clr-text-light); margin-left: 1px; vertical-align: middle;
      animation: blink 0.6s infinite;
    }
    .msg-row.user .tw-cursor { background: rgba(255,255,255,0.7); }
    @keyframes blink { 0%,100%{opacity:1} 50%{opacity:0} }

    .step-image { margin: 8px 0 4px; }
    .step-image img {
      max-width: 100%; max-height: 240px; border-radius: 8px; cursor: zoom-in;
      border: 1px solid var(--clr-border); object-fit: contain; background: var(--clr-bg-panel);
      display: block; transition: opacity 0.2s;
    }
    .step-image img:hover { opacity: 0.85; }

    .inter-step-dots {
      display: flex; gap: 4px; align-items: center; padding: 5px 2px; margin-top: 4px;
    }
    .inter-step-dots span {
      width: 5px; height: 5px; background: #b0bedc; border-radius: 50%;
      animation: tdot 1.1s infinite; display: inline-block;
    }
    .inter-step-dots span:nth-child(2) { animation-delay: 0.15s; }
    .inter-step-dots span:nth-child(3) { animation-delay: 0.30s; }
    @keyframes tdot { 0%,60%,100%{transform:translateY(0);background:var(--clr-border)} 30%{transform:translateY(-4px);background:var(--clr-text-light)} }

    .msg-sources {
      font-size: 11px; color: var(--clr-text-light); margin-top: 3px;
      padding-left: calc(var(--av) + var(--av-gap));
    }
    .msg-sources span { color: var(--clr-primary); }

    .feedback-row {
      display: flex; gap: 6px; margin-top: 4px; align-items: center;
      padding-left: calc(var(--av) + var(--av-gap));
    }
    .feedback-row > span { font-size: 11px; color: var(--clr-text-light); }
    .fb-btn {
      font-size: 11px; padding: 3px 10px; border-radius: 12px;
      border: 1px solid var(--clr-border); cursor: pointer; background: white;
      color: var(--clr-text-light); transition: all 0.15s; display: flex; align-items: center; gap: 4px;
    }
    .fb-btn:hover    { background: var(--clr-primary-light); border-color: var(--clr-primary); color: var(--clr-primary); }
    .fb-btn.confirmed{ background: #e6f4ea; border-color: #34a853; color: #34a853; pointer-events:none; }
    .fb-btn.dismissed{ display: none; }
    .fb-btn.loading  { opacity: 0.6; pointer-events: none; }

    .fb-panel {
      margin-top: 6px; margin-left: calc(var(--av) + var(--av-gap));
      background: var(--clr-bg-panel); border: 1px solid var(--clr-border); border-radius: 10px;
      padding: 10px 12px; max-width: 420px;
      animation: fadeIn 0.15s ease;
    }
    @keyframes fadeIn { from{opacity:0;transform:translateY(-4px)} to{opacity:1;transform:translateY(0)} }
    .fb-panel-title { font-size: 12px; color: var(--clr-text-main); font-weight: 500; margin-bottom: 8px; }
    .fb-reasons { display: flex; flex-direction: column; gap: 4px; margin-bottom: 10px; }
    .fb-reason {
      display: flex; align-items: center; gap: 7px;
      font-size: 12px; color: var(--clr-text-main); cursor: pointer; padding: 4px 6px;
      border-radius: 6px; transition: background 0.1s;
    }
    .fb-reason:hover { background: var(--clr-primary-light); }
    .fb-reason input[type="radio"] { accent-color: var(--clr-primary); cursor: pointer; }
    .fb-reason.selected { background: var(--clr-primary-light); color: var(--clr-primary); }
    .fb-comment {
      width: 100%; font-size: 12px; border: 1px solid var(--clr-border);
      border-radius: 6px; padding: 6px 8px; resize: none;
      font-family: inherit; color: var(--clr-text-main); outline: none;
      transition: border-color 0.15s;
    }
    .fb-comment:focus { border-color: var(--clr-primary); }
    .fb-comment::placeholder { color: var(--clr-text-light); }
    .fb-actions { display: flex; gap: 6px; margin-top: 8px; justify-content: flex-end; }
    .fb-submit {
      font-size: 11px; padding: 4px 12px; border-radius: 10px;
      background: var(--clr-primary); color: white; border: none; cursor: pointer;
      transition: opacity 0.15s;
    }
    .fb-submit:hover { opacity: 0.88; }
    .fb-cancel {
      font-size: 11px; padding: 4px 10px; border-radius: 10px;
      background: none; color: var(--clr-text-light); border: 1px solid var(--clr-border); cursor: pointer;
    }
    .fb-cancel:hover { background: var(--clr-bg-bot); }
    .spinner {
      width: 10px; height: 10px; border: 2px solid var(--clr-primary-light);
      border-top-color: var(--clr-primary); border-radius: 50%; animation: spin 0.6s linear infinite; display: inline-block;
    }
    @keyframes spin { to { transform: rotate(360deg); } }

    .typing-row { display: flex; gap: var(--av-gap); align-items: flex-end; align-self: flex-start; }
    .typing-content {
      background: var(--clr-bg-bot); border-radius: 18px; border-bottom-left-radius: 4px;
      padding: 10px 14px; display: flex; flex-direction: column; gap: 6px; min-width: 140px;
      border: 1px solid var(--clr-border);
    }
    .typing-dots { display: flex; gap: 5px; align-items: center; }
    .typing-dots span {
      width: 7px; height: 7px; background: #b0bedc; border-radius: 50%;
      animation: tdot 1.3s infinite; display: inline-block;
    }
    .typing-dots span:nth-child(2) { animation-delay: 0.15s; }
    .typing-dots span:nth-child(3) { animation-delay: 0.30s; }
    .typing-status { font-size: 11px; color: var(--clr-text-light); min-height: 14px; transition: opacity 0.25s; white-space: nowrap; }
    .typing-status.fade { opacity: 0; }

    #lightbox {
      display: none; position: fixed; top: 0; left: 0; right: 0; bottom: 0;
      background: rgba(0,0,0,0.88); z-index: 99999; align-items: center; justify-content: center; cursor: zoom-out;
    }
    #lightbox.open { display: flex; }
    #lightbox img  { max-width: 92vw; max-height: 92vh; border-radius: 8px; }
    #lightbox-close { position: absolute; top: 16px; right: 20px; color: white; font-size: 28px; cursor: pointer; background: none; border: none; }

    #input-area {
      padding: 10px 12px; border-top: 1px solid var(--clr-border);
      display: flex; gap: 8px; align-items: flex-end; flex-shrink: 0; background: white;
    }
    #user-input {
      flex: 1; border: 1.5px solid var(--clr-border); border-radius: 20px;
      padding: 8px 14px; font-size: 13px; resize: none; outline: none;
      line-height: 1.45; font-family: inherit;
      overflow-y: auto; max-height: 96px; scrollbar-width: none; -ms-overflow-style: none;
    }
    #user-input::-webkit-scrollbar { display: none; }
    #user-input:focus { border-color: var(--clr-primary); }

    #send-btn {
      width: 38px; height: 38px; background: var(--clr-primary); border: none; border-radius: 50%;
      cursor: pointer; flex-shrink: 0; display: flex; align-items: center; justify-content: center;
    }
    #send-btn:hover    { background: var(--clr-primary-dark); }
    #send-btn:disabled { background: #b0bedc; cursor: not-allowed; }
    #send-btn svg { width: 16px; height: 16px; fill: white; }

    #history-loading {
      position: absolute; top: 0; left: 0; right: 0; bottom: 0; background: white;
      display: flex; align-items: center; justify-content: center; flex-direction: column; gap: 10px; z-index: 10;
    }
    #history-loading .big-spinner {
      width: 26px; height: 26px; border: 3px solid var(--clr-primary-light);
      border-top-color: var(--clr-primary); border-radius: 50%; animation: spin 0.8s linear infinite;
    }
    #history-loading p { font-size: 13px; color: var(--clr-text-light); }

    @keyframes stepIn { from{opacity:0;transform:translateY(5px)} to{opacity:1;transform:translateY(0)} }
    .step-block { animation: stepIn 0.2s ease; }

    /* ERP-aligned compact skin. Keep class names stable for existing JS. */
    :root {
      --av: 24px;
      --av-gap: 7px;
      --clr-primary:       #002b63;
      --clr-primary-dark:  #001f49;
      --clr-primary-light: #eaf1fb;
      --clr-bg-page:       #eaeff7;
      --clr-bg-bot:        #ffffff;
      --clr-bg-panel:      #f7faff;
      --clr-text-main:     #002b63;
      --clr-text-soft:     #28466f;
      --clr-text-light:    #6f829f;
      --clr-border:        #d8e1f1;
      --clr-border-strong: #b9c8de;
    }

    html, body {
      background: var(--clr-bg-page);
      color: var(--clr-text-main);
    }

    #chat-container {
      background: var(--clr-bg-page);
    }

    #messages {
      flex: 1;
      overflow-y: auto;
      overflow-x: hidden;
      min-width: 0;
      padding: 10px 10px 8px;
      gap: 7px;
      display: flex;
      flex-direction: column;
      background:
        linear-gradient(#eaf0fa 0, #eaf0fa 1px, transparent 1px) 0 0 / 100% 26px,
        var(--clr-bg-page);
      scrollbar-color: #9db2d1 #edf3fb;
    }


    .date-sep {
      margin: 5px 0 3px;
      font-size: 10px;
      color: var(--clr-text-light);
      letter-spacing: 0.08em;
      text-transform: uppercase;
    }
    .date-sep::before, .date-sep::after { width: 22%; background: var(--clr-border-strong); }

    .history-label {
      padding: 3px 10px;
      background: rgba(255,255,255,0.72);
      border: 1px solid var(--clr-border);
      border-radius: 6px;
      color: var(--clr-text-light);
      font-size: 10px;
      letter-spacing: 0.04em;
    }

    .msg-row { max-width: min(90%, 600px); }
    .msg-inner { align-items: flex-start; }

    .bot-avatar, .user-avatar {
      width: var(--av);
      height: var(--av);
      margin-top: 2px;
      border-radius: 6px;
      border: 1px solid #c7d5e8;
      box-shadow: 0 1px 2px rgba(0, 43, 99, 0.08);
    }
    .bot-avatar { background: #ffffff; }
    .bot-avatar img { width: 18px; height: 18px; border-radius: 0; }
    .user-avatar {
      background: var(--clr-primary);
      color: #ffffff;
      font-size: 10px;
      border-color: var(--clr-primary);
    }
    .user-avatar img { border-radius: 5px; }

    .bubble {
      padding: 8px 10px;
      border-radius: 8px;
      font-size: 12px;
      line-height: 1.55;
      letter-spacing: 0;
      box-shadow: 0 1px 3px rgba(0, 43, 99, 0.06);
      overflow-wrap: anywhere;
      word-break: break-word;
      white-space: normal;
      max-width: 100%;
      min-width: 0;
    }
    .bubble pre,
    .bubble code {
      max-width: 100%;
      overflow-x: auto;
      white-space: pre-wrap;
      word-break: break-word;
    }
    .msg-row.bot .bubble {
      background: #ffffff;
      color: var(--clr-text-soft);
      border: 1px solid #cbd8ea;
      border-top-left-radius: 3px;
      border-bottom-left-radius: 8px;
    }
    .msg-row.user .bubble {
      background: var(--clr-primary);
      color: #ffffff;
      border: 1px solid var(--clr-primary);
      border-top-right-radius: 3px;
      border-bottom-right-radius: 8px;
      box-shadow: none;
    }

    .response-intro, .step-text { line-height: 1.55; }
    .response-intro { margin-bottom: 6px; }
    .step-block { margin: 4px 0; }

    .msg-time {
      margin-top: 3px;
      font-size: 9px;
      letter-spacing: 0.03em;
      color: var(--clr-text-light);
      opacity: 1;
    }

    .suggestions {
      gap: 5px;
      margin-top: 8px;
      padding-top: 7px;
    }
    .suggestion-btn, .chart-toggle, .fb-btn {
      border-radius: 6px;
      font-size: 11px;
      color: var(--clr-primary);
    }
    .suggestion-btn {
      padding: 5px 8px;
      background: #f8fbff;
    }

    .chart-question, .rank-chart, .fb-panel, .typing-content {
      border-radius: 8px;
      border-color: #cbd8ea;
      background: #ffffff;
    }

    .chart-actions {
      margin-left: calc(var(--av) + var(--av-gap));
      max-width: min(90%, 600px);
    }

    .step-image img {
      border-radius: 6px;
      border-color: #cbd8ea;
      background: #f8fbff;
    }

    .feedback-row {
      margin-top: 5px;
      gap: 5px;
    }
    .feedback-row > span {
      font-size: 10px;
      letter-spacing: 0.03em;
    }
    .fb-btn {
      padding: 2px 8px;
      background: #ffffff;
    }
    .fb-panel {
      padding: 9px 10px;
      max-width: 440px;
      box-shadow: 0 2px 6px rgba(0, 43, 99, 0.08);
    }
    .fb-panel-title, .fb-reason, .fb-comment { font-size: 11px; }
    .fb-submit, .fb-cancel {
      border-radius: 6px;
      font-size: 11px;
    }

    .typing-row { align-items: flex-start; }
    .typing-content {
      min-width: 150px;
      padding: 8px 10px;
      gap: 5px;
      box-shadow: 0 1px 3px rgba(0, 43, 99, 0.06);
    }
    .typing-status {
      font-size: 10px;
      color: var(--clr-text-light);
    }
    .typing-dots span, .inter-step-dots span {
      width: 5px;
      height: 5px;
      background: #9db2d1;
    }

    #input-area {
      padding: 8px 9px;
      gap: 7px;
      align-items: center;
      background: #f8fbff;
      border-top: 1px solid var(--clr-border-strong);
      box-shadow: 0 -2px 8px rgba(0, 43, 99, 0.05);
      width: 100%;
      box-sizing: border-box;
    }

    #user-input {
      min-height: 34px;
      max-height: 92px;
      padding: 8px 11px;
      background: #ffffff;
      border: 1px solid #9db2d1;
      border-radius: 8px;
      color: var(--clr-text-main);
      font-size: 12px;
      line-height: 1.4;
    }
    #user-input:focus {
      border-color: var(--clr-primary);
      box-shadow: inset 0 0 0 1px rgba(0, 43, 99, 0.12);
    }
    #user-input::placeholder {
      color: #6f829f;
    }

    #send-btn {
      width: 34px;
      height: 34px;
      border-radius: 8px;
      background: var(--clr-primary);
      box-shadow: 0 2px 5px rgba(0, 43, 99, 0.18);
    }
    #send-btn svg { width: 15px; height: 15px; }

    #history-loading {
      background: var(--clr-bg-page);
    }
    #history-loading .big-spinner {
      width: 22px;
      height: 22px;
      border-width: 2px;
    }
    #history-loading p {
      font-size: 11px;
      letter-spacing: 0.06em;
      text-transform: uppercase;
    }

    #session-strip {
      display: flex;
      align-items: center;
      gap: 8px;
      min-height: 30px;
      padding: 6px 10px;
      background: #f8fbff;
      border-bottom: 1px solid var(--clr-border);
      color: var(--clr-text-light);
      font-size: 10px;
      letter-spacing: 0.04em;
      text-transform: uppercase;
      flex-shrink: 0;
    }
    #session-strip .session-user {
      color: var(--clr-primary);
      font-weight: 700;
      max-width: 48%;
      overflow: hidden;
      text-overflow: ellipsis;
      white-space: nowrap;
    }
    #session-strip .session-dot {
      width: 4px;
      height: 4px;
      border-radius: 50%;
      background: #9db2d1;
      flex-shrink: 0;
    }
    #session-strip .session-history {
      overflow: hidden;
      text-overflow: ellipsis;
      white-space: nowrap;
    }

    #chat-main {
      flex: 1;
      min-height: 0;
      display: flex;
      overflow: hidden;
      background: var(--clr-bg-page);
    }

    #chat-content {
      flex: 1;
      min-width: 0;
      display: flex;
      flex-direction: column;
      min-height: 0;
      overflow: hidden;
    }

    #chat-sidebar {

      width: 150px;
      flex: 0 0 150px;
      padding: 8px 7px;
      overflow-y: auto;
      background: rgba(255,255,255,0.52);
      border-right: 1px solid var(--clr-border-strong);
      scrollbar-width: thin;
      scrollbar-color: #b9c8de transparent;
    }

    .side-action {
      width: 100%;
      min-height: 30px;
      display: flex;
      align-items: center;
      gap: 7px;
      padding: 6px 7px;
      margin-bottom: 4px;
      background: transparent;
      color: var(--clr-text-main);
      border: 1px solid transparent;
      border-radius: 7px;
      cursor: pointer;
      font-family: inherit;
      font-size: 11px;
      text-align: left;
      letter-spacing: 0.01em;
    }

    .side-action:hover, .side-action.active {
      background: #ffffff;
      border-color: var(--clr-border);
      box-shadow: 0 1px 3px rgba(0, 43, 99, 0.06);
    }

    .side-ico {
      width: 15px;
      flex: 0 0 15px;
      color: var(--clr-primary);
      text-align: center;
      font-size: 13px;
      line-height: 1;
    }

    #recent-search {
      width: 100%;
      height: 28px;
      margin: 5px 0 10px;
      padding: 0 8px;
      background: #ffffff;
      color: var(--clr-text-main);
      border: 1px solid var(--clr-border);
      border-radius: 7px;
      outline: none;
      font-family: inherit;
      font-size: 11px;
    }

    #recent-search:focus {
      border-color: var(--clr-primary);
    }

    .side-section {
      margin: 10px 0 5px;
      padding: 0 7px;
      color: var(--clr-text-main);
      font-size: 10px;
      font-weight: 700;
      letter-spacing: 0.06em;
      text-transform: uppercase;
    }

    #recent-list {
      display: flex;
      flex-direction: column;
      gap: 2px;
    }

    .recent-item {
      width: 100%;
      min-height: 28px;
      padding: 6px 7px;
      background: transparent;
      color: var(--clr-text-soft);
      border: 1px solid transparent;
      border-radius: 7px;
      cursor: pointer;
      font-family: inherit;
      font-size: 11px;
      line-height: 1.35;
      text-align: left;
      overflow: hidden;
      text-overflow: ellipsis;
      white-space: nowrap;
    }

    .recent-item:hover {
      background: #ffffff;
      color: var(--clr-primary);
      border-color: var(--clr-border);
    }

    .recent-empty {
      padding: 6px 7px;
      color: var(--clr-text-light);
      font-size: 10px;
      line-height: 1.45;
    }

    /* ── Chat Item with Pin + 3-dot Menu ─────────────────────────────────── */
    .chat-item-wrap {
      position: relative;
      display: flex;
      align-items: center;
      min-height: 32px;
      padding: 0;
      border-radius: 7px;
      cursor: pointer;
      font-family: inherit;
      font-size: 12px;
      line-height: 1.35;
      text-align: left;
      transition: background 0.12s;
    }
    .chat-item-wrap:hover {
      background: #eef3fa;
    }
    .chat-item-wrap.pinned {
      order: -1;
    }

    .chat-item-label {
      flex: 1;
      min-width: 0;
      padding: 7px 6px 7px 8px;
      overflow: hidden;
      text-overflow: ellipsis;
      white-space: nowrap;
      color: var(--clr-text-soft);
      user-select: none;
      pointer-events: none;
    }
    .chat-item-wrap.active .chat-item-label {
      color: var(--clr-primary);
      font-weight: 600;
    }

    .chat-item-actions {
      display: none;
      align-items: center;
      gap: 2px;
      padding-right: 4px;
      flex-shrink: 0;
    }
    .chat-item-wrap:hover .chat-item-actions {
      display: flex;
    }

    .chat-pin-btn {
      width: 22px; height: 22px;
      border: none; background: transparent;
      border-radius: 4px;
      cursor: pointer;
      display: flex; align-items: center; justify-content: center;
      font-size: 12px; line-height: 1;
      color: var(--clr-text-light);
      transition: all 0.12s;
      flex-shrink: 0;
    }
    .chat-pin-btn:hover {
      background: #dce4f0;
      color: var(--clr-primary);
    }
    .chat-pin-btn.pinned {
      color: #e8a020;
    }
    .chat-pin-btn.pinned:hover {
      background: #f5e6c8;
    }

    .chat-menu-btn {
      width: 22px; height: 22px;
      border: none; background: transparent;
      border-radius: 4px;
      cursor: pointer;
      display: flex; align-items: center; justify-content: center;
      font-size: 14px; line-height: 1;
      color: var(--clr-text-light);
      transition: all 0.12s;
      flex-shrink: 0;
      letter-spacing: -1px;
    }
    .chat-menu-btn:hover {
      background: #dce4f0;
      color: var(--clr-primary);
    }

    /* ── Dropdown Menu ────────────────────────────────────────────────────── */
    .chat-dropdown {
      position: absolute;
      right: 4px;
      top: 100%;
      z-index: 1000;
      min-width: 200px;
      background: #ffffff;
      border: 1px solid var(--clr-border);
      border-radius: 10px;
      box-shadow: 0 4px 16px rgba(0, 43, 99, 0.14);
      padding: 4px 0;
      display: none;
      animation: fadeIn 0.12s ease;
    }
    .chat-dropdown.open {
      display: block;
    }

    .chat-dropdown-item {
      display: flex;
      align-items: center;
      gap: 10px;
      width: 100%;
      padding: 8px 14px;
      border: none;
      background: transparent;
      font-family: inherit;
      font-size: 12px;
      color: var(--clr-text-main);
      cursor: pointer;
      text-align: left;
      transition: background 0.08s;
      line-height: 1.4;
    }
    .chat-dropdown-item:hover {
      background: var(--clr-primary-light);
    }
    .chat-dropdown-item .dd-icon {
      width: 16px;
      flex-shrink: 0;
      text-align: center;
      font-size: 14px;
      color: var(--clr-text-light);
    }
    .chat-dropdown-item.danger {
      color: #d93025;
    }
    .chat-dropdown-item.danger .dd-icon {
      color: #d93025;
    }
    .chat-dropdown-item.danger:hover {
      background: #fce8e6;
    }

    .chat-dropdown-divider {
      height: 1px;
      background: var(--clr-border);
      margin: 4px 8px;
    }

    /* ── Inline Rename ────────────────────────────────────────────────────── */
    .chat-rename-input {
      flex: 1;
      min-width: 0;
      margin: 4px 6px 4px 8px;
      padding: 4px 6px;
      border: 1.5px solid var(--clr-primary);
      border-radius: 5px;
      font-family: inherit;
      font-size: 12px;
      color: var(--clr-text-main);
      background: #ffffff;
      outline: none;
    }

    /* ── Pin icon in label ────────────────────────────────────────────────── */
    .chat-pin-indicator {
      display: none;
      font-size: 10px;
      color: #e8a020;
      margin-right: 3px;
    }
    .chat-item-wrap.pinned .chat-pin-indicator {
      display: inline;
    }

    /* ── Responsive ───────────────────────────────────────────────────────── */
    @media (min-width: 900px) {
      .chat-item-wrap {
        min-height: 46px;
        border-radius: 10px;
        font-size: 17px;
      }
      .chat-item-label {
        padding: 11px 10px 11px 13px;
      }
      .chat-pin-btn, .chat-menu-btn {
        width: 30px; height: 30px;
        font-size: 16px;
        border-radius: 6px;
      }
      .chat-menu-btn {
        font-size: 18px;
      }
      .chat-dropdown {
        min-width: 260px;
        border-radius: 12px;
      }
      .chat-dropdown-item {
        padding: 10px 16px;
        font-size: 16px;
        gap: 12px;
      }
      .chat-dropdown-item .dd-icon {
        width: 20px;
        font-size: 17px;
      }
      .chat-rename-input {
        font-size: 16px;
        padding: 6px 8px;
        margin: 6px 10px 6px 13px;
      }
    }

    @media (max-width: 460px) {
      .chat-item-wrap {
        min-height: 28px;
        font-size: 10px;
      }
      .chat-item-label {
        padding: 6px 5px 6px 7px;
      }
      .chat-pin-btn, .chat-menu-btn {
        width: 20px; height: 20px;
        font-size: 10px;
      }
      .chat-menu-btn {
        font-size: 12px;
      }
      .chat-dropdown {
        min-width: 170px;
      }
      .chat-dropdown-item {
        padding: 6px 10px;
        font-size: 10px;
        gap: 8px;
      }
      .chat-dropdown-item .dd-icon {
        width: 14px;
        font-size: 12px;
      }
      .chat-rename-input {
        font-size: 10px;
        padding: 3px 5px;
        margin: 3px 5px 3px 7px;
      }
    }

    @media (max-width: 460px) {

      #chat-sidebar {
        width: 116px;
        flex-basis: 116px;
      }
      .side-action, .recent-item, #recent-search {
        font-size: 10px;
      }
    }

    /* Readability bump for ERP desktop: text was too small at normal zoom. */
    #session-strip {
      min-height: 34px;
      font-size: 11px;
    }

    #chat-sidebar {
      width: 172px;
      flex-basis: 172px;
      padding: 9px 8px;
    }

    .side-action {
      min-height: 34px;
      padding: 7px 8px;
      font-size: 12px;
    }

    .side-ico {
      width: 16px;
      flex-basis: 16px;
      font-size: 14px;
    }

    #recent-search {
      height: 32px;
      font-size: 12px;
    }

    .side-section {
      font-size: 11px;
      margin-top: 12px;
    }

    .recent-item {
      min-height: 32px;
      font-size: 12px;
      padding: 7px 8px;
    }

    .recent-empty {
      font-size: 11px;
    }

    .bubble {
      font-size: 13px;
      line-height: 1.6;
      padding: 9px 11px;
      overflow-wrap: anywhere;
      word-break: break-word;
      white-space: normal;
      max-width: 100%;
      min-width: 0;
    }
    .bubble pre,
    .bubble code {
      max-width: 100%;
      overflow-x: auto;
      white-space: pre-wrap;
      word-break: break-word;
    }

    .msg-time {
      font-size: 10px;
    }
    .load-more-wrap {
      display: flex;
      justify-content: center;
      margin: 4px 0 8px;
    }
    .load-more-btn {
      border: 1px solid var(--clr-border-strong);
      background: #ffffff;
      color: var(--clr-primary);
      border-radius: 6px;
      padding: 6px 10px;
      font: inherit;
      font-size: 12px;
      cursor: pointer;
    }
    .load-more-btn:hover {
      background: #eef4ff;
    }

    #user-input {
      min-height: 38px;
      font-size: 13px;
      padding: 9px 12px;
    }

    #send-btn {
      width: 38px;
      height: 38px;
    }

    /* Large desktop scale: roughly double the compact widget UI. */
    @media (min-width: 900px) {
      :root {
        --av: 42px;
        --av-gap: 14px;
      }

      #session-strip {
        min-height: 48px;
        padding: 10px 18px;
        font-size: 16px;
      }

      #session-strip .session-dot {
        width: 7px;
        height: 7px;
      }

      #chat-sidebar {
        width: 280px;
        flex: 0 0 280px;
        padding: 16px 14px;
      }

      .side-action {
        min-height: 50px;
        gap: 12px;
        padding: 12px 14px;
        border-radius: 10px;
        font-size: 18px;
      }

      .side-ico {
        width: 22px;
        flex-basis: 22px;
        font-size: 22px;
      }

      #recent-search {
        height: 46px;
        margin: 10px 0 18px;
        padding: 0 14px;
        border-radius: 10px;
        font-size: 17px;
      }

      .side-section {
        margin: 18px 0 10px;
        padding: 0 12px;
        font-size: 15px;
      }

      .recent-item {
        min-height: 46px;
        padding: 11px 13px;
        border-radius: 10px;
        font-size: 17px;
      }

      .recent-empty {
        padding: 10px 12px;
        font-size: 15px;
      }

      #messages {
        padding: 18px 20px 14px;
        gap: 14px;
      }

      .bot-avatar, .user-avatar {
        width: var(--av);
        height: var(--av);
        border-radius: 10px;
      }

      .bot-avatar img {
        width: 30px;
        height: 30px;
      }

      .user-avatar {
        font-size: 16px;
      }

      .msg-row {
        max-width: min(88%, 880px);
      }

      .bubble {
        padding: 15px 18px;
        border-radius: 14px;
        font-size: 22px;
        line-height: 1.58;
        overflow-wrap: anywhere;
        word-break: break-word;
        white-space: normal;
        max-width: 100%;
        min-width: 0;
      }
      .bubble pre,
      .bubble code {
        max-width: 100%;
        overflow-x: auto;
        white-space: pre-wrap;
        word-break: break-word;
      }

      .response-intro, .step-text {
        line-height: 1.58;
      }

      .msg-time {
        margin-top: 7px;
        font-size: 15px;
      }

      .history-label, .date-sep {
        font-size: 15px;
      }

      .typing-content {
        min-width: 240px;
        padding: 14px 18px;
        border-radius: 14px;
      }

      .typing-status {
        font-size: 16px;
      }

      .typing-dots span, .inter-step-dots span {
        width: 9px;
        height: 9px;
      }

      .suggestion-btn, .chart-toggle, .fb-btn {
        border-radius: 10px;
        font-size: 17px;
      }

      .feedback-row > span {
        font-size: 15px;
      }

      #input-area {
        padding: 14px 16px;
        gap: 12px;
      }

      #user-input {
        min-height: 58px;
        max-height: 150px;
        padding: 15px 18px;
        border-radius: 12px;
        font-size: 20px;
      }

      #send-btn {
        width: 58px;
        height: 58px;
        border-radius: 12px;
      }

      #send-btn svg {
        width: 25px;
        height: 25px;
      }
    }
  </style>
  <script src="https://cdn.jsdelivr.net/npm/marked/marked.min.js"></script>
</head>
<body>
<div id="lightbox">
  <button id="lightbox-close" onclick="closeLightbox()">✕</button>
  <img id="lightbox-img" src="" alt=""/>
</div>
<div id="chat-container">
  <div id="history-loading">
    <div class="big-spinner"></div>
    <p>Loading...</p>
  </div>
  <div id="session-strip"></div>
  <div id="chat-main">
    <aside id="chat-sidebar">
      <button class="side-action active" type="button" onclick="startNewChat()">
        <span class="side-ico">+</span><span>New chat</span>
      </button>
      <input id="recent-search" type="text" placeholder="Search chats">
      <div class="side-section">Recent</div>
      <div id="recent-list">
        <div class="recent-empty">No chat history yet.</div>
      </div>
    </aside>
    <div id="chat-content">
      <div id="messages"></div>
      <div id="input-area">
        <textarea id="user-input" placeholder="Ask a question..." rows="1"></textarea>
        <button id="send-btn">
          <svg viewBox="0 0 24 24"><path d="M2 21l21-9L2 3v7l15 2-15 2v7z"/></svg>
        </button>
      </div>
    </div>
  </div>

</div>
<script>
  //── Config ──────────────────────────────────────────────────────────────────
  // Không gọi thẳng ra AI API ngoài nữa. Mọi request đi qua inc_ajax_ai_assistant.cfm (cùng thư mục),
  // theo đúng cấu trúc inc_ajax_xxx.cfm (action + cfswitch) đang dùng trong hệ thống.
  // File proxy giữ API key ở server nên key không bao giờ lộ ra client/View Source.
  const AJAX_URL      = "inc_ajax_ai_assistant.cfm";
  const SHOW_SOURCES  = false;

  // Helper: gọi 1 "action" trong inc_ajax_ai_assistant.cfm, body dạng form-urlencoded (chuẩn cfparam)
  function callAjax(action, params={}, timeoutMs=7000){
    const body = new URLSearchParams({action, ...params});
    return fetchWithTimeout(AJAX_URL, {
      method: "POST",
      headers: {"Content-Type": "application/x-www-form-urlencoded"},
      body: body.toString()
    }, timeoutMs);
  }

  // Helper: build URL GET cho ảnh (dùng trong <img src>, không thể POST được)
  function ajaxImageUrl(imagePath){
    return `${AJAX_URL}?action=get_image&image_path=${encodeURIComponent(imagePath)}`;
  }

  //── ERP session — injected server-side from cookies ─────────────────────────
  <cfoutput>
  const USER_ID    = "#JSStringFormat(cookie.cookuserloginid)#";
  const COMPANY_ID = "#JSStringFormat(cookie.cookmfnunique)#";   // masterfn = history namespace
  const MASTERFN   = "#JSStringFormat(cookie.cookmfnunique)#";
  const COMPANYFN  = "#JSStringFormat(cookie.cookcfnunique)#";
  const LANG       = "#JSStringFormat(cookie.cooklang)#";
  </cfoutput>

  function fetchWithTimeout(url, options={}, timeoutMs=7000){
    const controller = new AbortController();
    const timer = setTimeout(() => controller.abort(), timeoutMs);
    return fetch(url, {...options, signal: controller.signal})
      .finally(() => clearTimeout(timer));
  }

  function resolveStepImageSrc(img){
    if(!img) return null;
    const src = String(img).trim().replace(/\\/g, "/");
    if(!src) return null;
    if(/^data:/i.test(src) || /^https?:\/\//i.test(src) || src.startsWith("/")){
      return src;
    }
    const safePath = src.split("/").filter(Boolean).join("/");
    return ajaxImageUrl(safePath);
  }

  function displayUserName(){
    const raw = (USER_ID || "User").trim();
    const cleaned = raw.replace(/[_\-.]+/g, " ").replace(/\s+/g, " ").trim();
    if(!cleaned) return "User";
    return cleaned.split(" ").map(part => part ? part.charAt(0).toUpperCase() + part.slice(1) : "").join(" ");
  }

  function updateSessionStrip(historyCount){
    const strip = document.getElementById("session-strip");
    if(!strip) return;
    const count = Number(historyCount || 0);
    const historyText = count > 0
      ? `${count} previous message${count === 1 ? "" : "s"} loaded`
      : "No previous messages yet";
    strip.innerHTML = `
      <span class="session-user">${escHtml(displayUserName())}</span>
      <span class="session-dot"></span>
      <span class="session-history">${historyText}</span>
    `;
  }

  let recentChats = [];
  let activeRecentId = "";
  let openDropdownId = null; // only one dropdown open at a time
  let currentSessionId = "";
  let currentSessionTitle = "";
  let currentSessionMessages = [];
  let currentSessionHasMore = false;
  let currentSessionOldestId = null;
  const HISTORY_PAGE_SIZE = 5;
  const SESSION_KEY = `erp_ai_current_session_${USER_ID}_${COMPANY_ID}`;

  function getNewSessionId(){
    if(window.crypto?.randomUUID) return window.crypto.randomUUID();
    return `sess-${Date.now()}-${Math.random().toString(16).slice(2)}`;
  }

  function setCurrentSession(id){
    currentSessionId = id || "";
    try{
      if(currentSessionId) localStorage.setItem(SESSION_KEY, currentSessionId);
      else localStorage.removeItem(SESSION_KEY);
    }catch(e){}
  }

  function shortenTitle(text){
    const clean = (text || "").replace(/\s+/g, " ").trim();
    if(!clean) return "Untitled chat";
    return clean.length > 42 ? clean.slice(0, 39) + "..." : clean;
  }

  let activeDropdownEl = null; // the floating dropdown element appended to body

  function closeAllDropdowns(){
    if(activeDropdownEl){
      activeDropdownEl.remove();
      activeDropdownEl = null;
    }
    openDropdownId = null;
  }

  function toggleDropdown(chatId, btnEl){
    if(openDropdownId === chatId){
      closeAllDropdowns();
      return;
    }
    closeAllDropdowns();

    // Get the original dropdown template from sidebar
    const origDropdown = document.getElementById(`dd-${chatId}`);
    if(!origDropdown) return;

    // Clone it so we can append to body (avoid sidebar overflow clipping)
    const clone = origDropdown.cloneNode(true);
    clone.id = `dd-floating-${chatId}`;
    clone.classList.add("open");
    clone.style.position = "fixed";
    clone.style.zIndex = "99999";
    clone.style.display = "block";

    // Calculate position using getBoundingClientRect
    const rect = btnEl.getBoundingClientRect();
    const menuHeight = clone.offsetHeight || 220; // fallback estimate
    const spaceBelow = window.innerHeight - rect.bottom;
    const spaceAbove = rect.top;

    if (spaceBelow < menuHeight && spaceAbove > menuHeight) {
      // Open upward
      clone.style.top = (rect.top - menuHeight) + "px";
      clone.style.bottom = "auto";
    } else {
      // Open downward (default)
      clone.style.top = rect.bottom + "px";
      clone.style.bottom = "auto";
    }

    // Align right edge with button
    clone.style.right = (window.innerWidth - rect.right) + "px";
    clone.style.left = "auto";

    // Ensure menu doesn't go off-screen left
    const cloneRect = clone.getBoundingClientRect();
    if(cloneRect.left < 0){
      clone.style.left = "8px";
      clone.style.right = "auto";
    }

    // Attach event listeners to cloned dropdown items
    clone.querySelectorAll(".chat-dropdown-item").forEach(item => {
      item.addEventListener("click", e => {
        e.stopPropagation();
        const action = item.dataset.action;
        switch(action){
          case "share": shareChat(chatId); break;
          case "delete": deleteChat(chatId); break;
        }
      });
    });

    document.body.appendChild(clone);
    activeDropdownEl = clone;
    openDropdownId = chatId;
  }


  function togglePin(chatId){
    const item = recentChats.find(c => c.id === chatId);
    if(!item) return;
    item.pinned = !item.pinned;
    // Move pinned items to top
    recentChats.sort((a, b) => {
      if(a.pinned && !b.pinned) return -1;
      if(!a.pinned && b.pinned) return 1;
      return 0;
    });
    renderRecentChats(recentSearchEl ? recentSearchEl.value : "");
    closeAllDropdowns();
  }

  function startRename(chatId){
    const wrap = document.getElementById(`wrap-${chatId}`);
    if(!wrap) return;
    const label = wrap.querySelector(".chat-item-label");
    const currentTitle = label.textContent.replace(/^📌\s*/, "").trim();
    const input = document.createElement("input");
    input.type = "text";
    input.className = "chat-rename-input";
    input.value = currentTitle;
    input.autofocus = true;
    label.style.display = "none";
    wrap.querySelector(".chat-item-actions").style.display = "none";
    wrap.insertBefore(input, label.nextSibling);
    input.focus();
    input.select();

    function finishRename(){
      const newTitle = input.value.trim() || currentTitle;
      const item = recentChats.find(c => c.id === chatId);
      if(item){
        item.title = shortenTitle(newTitle);
        item.full = newTitle;
      }
      // Call API to rename session on server
      callAjax("sessions_rename", {session_id: chatId, title: newTitle, user_id: USER_ID, company_id: COMPANY_ID})
        .catch(e => console.error("Rename session error:", e));
      renderRecentChats(recentSearchEl ? recentSearchEl.value : "");
      closeAllDropdowns();
    }

    input.addEventListener("blur", finishRename);
    input.addEventListener("keydown", e => {
      if(e.key === "Enter"){ e.preventDefault(); input.blur(); }
      if(e.key === "Escape"){ e.preventDefault(); input.value = currentTitle; input.blur(); }
    });
  }

  async function deleteChat(chatId){
    const item = recentChats.find(c => c.id === chatId);
    if(!item) return;
    const wasActive = activeRecentId === chatId;
    const previousChats = recentChats.slice();
    recentChats = recentChats.filter(c => c.id !== chatId);
    if(wasActive){
      activeRecentId = "";
      setCurrentSession("");
      currentSessionMessages = [];
      currentSessionHasMore = false;
      currentSessionOldestId = null;
      msgEl.innerHTML = "";
      updateSessionStrip(recentChats.length);
      addBotMessage(`Hi ${displayUserName()}! I'm ready for a new chat. What would you like to do?`,[],new Date().toISOString());
    }
    renderRecentChats(recentSearchEl ? recentSearchEl.value : "");
    closeAllDropdowns();
    try{
      const res = await callAjax("sessions_delete", {session_id: item.id, user_id: USER_ID, company_id: COMPANY_ID}, 6000);
      if(!res.ok) throw new Error(`HTTP ${res.status}`);
    }catch(e){
      recentChats = previousChats;
      renderRecentChats(recentSearchEl ? recentSearchEl.value : "");
      if(wasActive) openRecentChat(chatId);
      addBotMessage("Could not delete that conversation. Please try again.",[],new Date().toISOString());
    }
  }

  function archiveChat(chatId){
    const item = recentChats.find(c => c.id === chatId);
    if(!item) return;
    item.archived = true;
    recentChats = recentChats.filter(c => !c.archived);
    if(activeRecentId === chatId){
      activeRecentId = "";
      setCurrentSession("");
      currentSessionMessages = [];
      currentSessionHasMore = false;
      currentSessionOldestId = null;
      msgEl.innerHTML = "";
      updateSessionStrip(recentChats.length);
      addBotMessage(`Hi ${displayUserName()}! I'm ready for a new chat. What would you like to do?`,[],new Date().toISOString());
    }
    renderRecentChats(recentSearchEl ? recentSearchEl.value : "");
    closeAllDropdowns();
  }

  function shareChat(chatId){
    const item = recentChats.find(c => c.id === chatId);
    if(!item) return;
    const text = `${item.title}\n\n${(item.messages || []).map(m => `${m.role}: ${m.content}`).join("\n")}`;
    if(navigator.clipboard){
      navigator.clipboard.writeText(text).then(() => {
        const toast = document.createElement("div");
        toast.textContent = "✓ Copied to clipboard!";
        toast.style.cssText = "position:fixed;bottom:20px;left:50%;transform:translateX(-50%);background:#002b63;color:white;padding:8px 16px;border-radius:8px;font-size:13px;z-index:99999;animation:fadeIn 0.2s ease;";
        document.body.appendChild(toast);
        setTimeout(() => toast.remove(), 2000);
      });
    }
    closeAllDropdowns();
  }

  function renderRecentChats(filterText=""){
    if(!recentEl) return;
    const term = (filterText || "").toLowerCase().trim();
    const items = recentChats.filter(item => !term || item.title.toLowerCase().includes(term));

    if(!items.length){
      recentEl.innerHTML = `<div class="recent-empty">${recentChats.length ? "No matching chats." : "No chat history yet."}</div>`;
      return;
    }

    recentEl.innerHTML = items.map((item, idx) => {
      const isActive = item.id === activeRecentId;
      const isPinned = item.pinned;
      const pinIndicator = isPinned ? '<span class="chat-pin-indicator">📌</span>' : '';
      return `
        <div class="chat-item-wrap${isActive ? " active" : ""}${isPinned ? " pinned" : ""}" id="wrap-${item.id}" data-chat-id="${item.id}">
          <span class="chat-item-label" title="${escHtml(item.full)}">${pinIndicator}${escHtml(item.title)}</span>
          <div class="chat-item-actions">
            <button class="chat-menu-btn" data-action="menu" title="More">⋮</button>
          </div>
          <div class="chat-dropdown" id="dd-${item.id}">
            <button class="chat-dropdown-item" data-action="share"><span class="dd-icon">↗</span> Share</button>
            <div class="chat-dropdown-divider"></div>
            <button class="chat-dropdown-item danger" data-action="delete"><span class="dd-icon">×</span> Delete</button>
          </div>
        </div>
      `;
    }).join("");

    // Attach event listeners
    recentEl.querySelectorAll(".chat-item-wrap").forEach(wrap => {
      const chatId = wrap.dataset.chatId;

      // Click on wrap = open chat
      wrap.addEventListener("click", e => {
        // Don't open if clicking on action buttons or dropdown
        if(e.target.closest(".chat-item-actions") || e.target.closest(".chat-dropdown")) return;
        const item = recentChats.find(c => c.id === chatId);
        if(item) openRecentChat(item.id);
      });

      // Menu button
      const menuBtn = wrap.querySelector("[data-action='menu']");
      if(menuBtn){
        menuBtn.addEventListener("click", e => {
          e.stopPropagation();
          toggleDropdown(chatId, menuBtn);
        });
      }

      // Dropdown items
      const dropdown = wrap.querySelector(".chat-dropdown");
      if(dropdown){
        dropdown.querySelectorAll(".chat-dropdown-item").forEach(item => {
          item.addEventListener("click", e => {
            e.stopPropagation();
            const action = item.dataset.action;
            switch(action){
              case "share": shareChat(chatId); break;
              case "delete": deleteChat(chatId); break;
            }
          });
        });
      }
    });
  }

  // Close dropdown when clicking outside
  document.addEventListener("click", e => {
    if(!e.target.closest(".chat-item-wrap")){
      closeAllDropdowns();
    }
  });


  function buildRecentChats(sessionRows){
    recentChats = [];
    const rows = sessionRows || [];

    rows.forEach((item) => {
      const titleSource = (item.title || item.first_user_msg || "").trim();
      const full = titleSource || "Untitled chat";
      recentChats.unshift({
        id: item.session_id,
        sessionId: item.session_id,
        title: shortenTitle(titleSource || full),
        full,
        messages: [],
        msgCount: Number(item.msg_count || 0),
        createdAt: item.created_at,
        updatedAt: item.updated_at,
        firstUserMsg: item.first_user_msg || "",
        _cachedHtml: "",
        _loadedAt: ""
      });
    });

    recentChats = recentChats.slice(0, 18);
    renderRecentChats(recentSearchEl ? recentSearchEl.value : "");
  }

  async function loadConversationMessages(sessionId, beforeId=null, appendOlder=false){
    if(!sessionId) return {history: [], has_more: false, oldest_id: null};
    const payload = {
      user_id: USER_ID,
      company_id: COMPANY_ID,
      session_id: sessionId,
      limit: HISTORY_PAGE_SIZE
    };
    if(beforeId) payload.before_id = beforeId;

    const res = await callAjax("chat_history", payload, 6000);
    if(!res.ok) throw new Error(`HTTP ${res.status}`);

    const data = await res.json();
    const rows = (data.history || []).slice().reverse();
    if(appendOlder){
      currentSessionMessages = rows.concat(currentSessionMessages);
    } else {
      currentSessionMessages = rows;
    }
    currentSessionHasMore = !!data.has_more;
    currentSessionOldestId = currentSessionMessages.length ? currentSessionMessages[0].id : null;
    const session = recentChats.find(item => item.id === sessionId);
    if(session){
      session.messages = currentSessionMessages.slice();
      session.msgCount = Math.max(session.msgCount || 0, currentSessionMessages.length);
      session.hasMore = currentSessionHasMore;
      session.oldestId = currentSessionOldestId;
      session._loadedAt = new Date().toISOString();
      session._cachedHtml = "";
    }
    return data;
  }

  // Cache rendered HTML for recent chats to avoid re-rendering
  let chatHtmlCache = {};

  function renderHistoryRows(rows, labelText, showLoadMore=true){
    msgEl.innerHTML = "";
    const list = rows || [];
    const fragment = document.createDocumentFragment();
    if(labelText){
      const lbl=document.createElement("div");
      lbl.className="history-label";
      lbl.textContent=labelText;
      fragment.appendChild(lbl);
    }
    if(showLoadMore && currentSessionHasMore && currentSessionOldestId){
      const moreWrap = document.createElement("div");
      moreWrap.className = "load-more-wrap";
      const moreBtn = document.createElement("button");
      moreBtn.type = "button";
      moreBtn.className = "load-more-btn";
      moreBtn.textContent = "Load older messages";
      moreBtn.addEventListener("click", () => loadOlderMessages());
      moreWrap.appendChild(moreBtn);
      fragment.appendChild(moreWrap);
    }
    let lastDate="";
    list.forEach(item=>{
      const d=formatDate(item.timestamp);
      if(d!==lastDate){
        const sep=document.createElement("div");
        sep.className="date-sep";
        sep.textContent=d;
        fragment.appendChild(sep);
        lastDate=d;
      }
      if(item.role==="user"){
        const row=document.createElement("div"); row.className="msg-row user";
        const inner=document.createElement("div"); inner.className="msg-inner";
        inner.innerHTML=`${userAvatarHtml()}<div class="bubble">${escHtml(item.content)}</div>`;
        row.appendChild(inner);
        if(item.timestamp){ const t=document.createElement("div"); t.className="msg-time"; t.textContent=formatTime(item.timestamp); row.appendChild(t); }
        fragment.appendChild(row);
      } else {
        const row=document.createElement("div"); row.className="msg-row bot";
        const inner=document.createElement("div"); inner.className="msg-inner";
        const avatar=document.createElement("div"); avatar.className="bot-avatar"; avatar.innerHTML='<svg width="18" height="18" viewBox="0 0 32 32" fill="none" xmlns="http://www.w3.org/2000/svg"><rect width="32" height="32" rx="6" fill="#1a73e8"/><text x="16" y="22" text-anchor="middle" fill="white" font-size="18" font-weight="bold" font-family="Arial">AI</text></svg>';
        const bubble=document.createElement("div"); bubble.className="bubble";
        renderMessageContent(bubble, item.content);
        inner.appendChild(avatar); inner.appendChild(bubble);
        row.appendChild(inner);
        if(item.timestamp){ const t=document.createElement("div"); t.className="msg-time"; t.textContent=formatTime(item.timestamp); row.appendChild(t); }
        fragment.appendChild(row);
      }
    });
    msgEl.appendChild(fragment);
    smoothScroll();
  }

  async function loadOlderMessages(){
    if(!currentSessionId || !currentSessionOldestId || !currentSessionHasMore) return;
    const prevScrollHeight = msgEl.scrollHeight;
    const prevScrollTop = msgEl.scrollTop;
    try{
      await loadConversationMessages(currentSessionId, currentSessionOldestId, true);
      renderHistoryRows(currentSessionMessages, `Conversation - ${currentSessionTitle}`, true);
      msgEl.scrollTop = msgEl.scrollHeight - prevScrollHeight + prevScrollTop;
      updateSessionStrip(currentSessionMessages.length);
    }catch(e){
      addBotMessage("Could not load earlier messages right now.",[],new Date().toISOString());
    }
  }

  async function openRecentChat(recentId){
    const item = recentChats.find(chat => chat.id === recentId);
    if(!item) return;
    activeRecentId = item.id;
    setCurrentSession(item.id);
    currentSessionTitle = item.title || item.full || "Untitled chat";
    currentSessionMessages = [];
    currentSessionHasMore = false;
    currentSessionOldestId = null;
    // Optimize: only update active class instead of re-rendering entire sidebar
    document.querySelectorAll(".chat-item-wrap.active").forEach(el => el.classList.remove("active"));
    const activeWrap = document.getElementById(`wrap-${recentId}`);
    if(activeWrap) activeWrap.classList.add("active");
    msgEl.innerHTML = "";
    let typing = null;
    try{
      if(Array.isArray(item.messages) && item.messages.length){
        currentSessionMessages = item.messages.slice();
        currentSessionHasMore = !!item.hasMore;
        currentSessionOldestId = item.oldestId || (currentSessionMessages.length ? currentSessionMessages[0].id : null);
      } else {
        updateSessionStrip(0);
        typing = addTypingIndicator();
        typing.setStatus("Loading conversation...");
        await loadConversationMessages(item.id, null, false);
        typing.remove();
      }
      renderHistoryRows(currentSessionMessages, `Conversation - ${item.title}`, true);
      item._cachedHtml = msgEl.innerHTML;
      updateSessionStrip(currentSessionMessages.length);
    }catch(e){
      if(typing) typing.remove();
      renderHistoryRows([], `Conversation - ${item.title}`, false);
      addBotMessage("Could not load that conversation yet. Please try again.",[],new Date().toISOString());
    }
    inputEl.value = "";
    inputEl.style.height = "auto";
    inputEl.focus();
  }

  async function startNewChat(){
    activeRecentId = "";
    const sessionId = getNewSessionId();
    setCurrentSession(sessionId);
    currentSessionTitle = "Untitled chat";
    currentSessionMessages = [];
    currentSessionHasMore = false;
    currentSessionOldestId = null;
    try{
      const res = await callAjax("sessions_create", {session_id: sessionId, user_id: USER_ID, company_id: COMPANY_ID, title: "Untitled chat"}, 5000);
      if(res.ok){
        const created = await res.json();
        recentChats.unshift({
          id: created.session_id || sessionId,
          sessionId: created.session_id || sessionId,
          title: shortenTitle(created.title || "Untitled chat"),
          full: created.title || "Untitled chat",
          messages: [],
          msgCount: 0,
          createdAt: new Date().toISOString(),
          updatedAt: new Date().toISOString(),
          firstUserMsg: ""
        });
      }
    }catch(e){}
    renderRecentChats(recentSearchEl ? recentSearchEl.value : "");
    msgEl.innerHTML = "";
    updateSessionStrip(0);
    addBotMessage(`Hi ${displayUserName()}! I'm ready for a new chat. What would you like to do?`,[],new Date().toISOString());
    inputEl.value = "";
    inputEl.style.height = "auto";
    inputEl.focus();
  }


  // Render markdown safely — falls back to escaped text if marked.js unavailable
  function normalizeAssistantText(text){
    let t = String(text || "").replace(/\r\n/g, "\n");
    if(/\[(SCM Overview|Demand Forecast|Product Trend|Sales Forecast)\]/i.test(t)){
      t = t
        .replace(/^\s*-\s+/gm, "")
        .replace(/^\s*•\s+/gm, "")
        .replace(/^\s*\[SCM Overview\]\s*/i, "**SCM Overview:** ")
        .replace(/^\s*\[Demand Forecast\]\s*/i, "**Demand Forecast:** ")
        .replace(/^\s*\[Product Trend\]\s*/i, "**Product Trend:** ")
        .replace(/^\s*\[Sales Forecast\]\s*/i, "**Sales Forecast:** ");
    }
    return t;
  }

  function renderMarkdown(text){
    if(!text) return "";
    const normalized = normalizeAssistantText(text);
    if(window.marked){ marked.setOptions({breaks:true}); return marked.parse(normalized); }
    return normalized.replace(/&/g,"&amp;").replace(/</g,"&lt;").replace(/>/g,"&gt;").replace(/\n/g,"<br>");
  }

  function splitSuggestedText(text){
    const queries = [];
    const re = /\[([^\]]+)\]\(query:([^)]+)\)/g;
    let match;
    while((match = re.exec(text || "")) !== null){
      queries.push({label: match[1].trim(), query: decodeURIComponent(match[2]).trim()});
    }
    if(!queries.length) return {body:text || "", queries};

    const lines = (text || "").split(/\r?\n/);
    const start = lines.findIndex(line => line.includes("(query:") || line.toLowerCase().includes("suggested"));
    let body = start >= 0 ? lines.slice(0, start).join("\n") : text;
    body = body.replace(/\n?---\s*$/g, "").trim();
    return {body, queries};
  }

  function renderTextWithImages(el, text){
    const content = String(text || "");
    const imgRe = /\[\[IMG:([^\]]+)\]\]/g;
    let lastIndex = 0;
    let match;
    let wroteAny = false;

    while((match = imgRe.exec(content)) !== null){
      const segment = content.slice(lastIndex, match.index).trim();
      if(segment){
        const wrap = document.createElement("div");
        wrap.innerHTML = renderMarkdown(segment);
        el.appendChild(wrap);
        wroteAny = true;
      }

      const src = resolveStepImageSrc(match[1]);
      if(src){
        const imgWrap = document.createElement("div");
        imgWrap.className = "step-image";
        const imgEl = document.createElement("img");
        imgEl.src = src;
        imgEl.alt = "step illustration";
        imgEl.loading = "lazy";
        imgEl.addEventListener("click", () => openLightbox(src));
        imgEl.addEventListener("error", () => { imgWrap.style.display = "none"; });
        imgWrap.appendChild(imgEl);
        el.appendChild(imgWrap);
        wroteAny = true;
      }

      lastIndex = imgRe.lastIndex;
    }

    const tail = content.slice(lastIndex).trim();
    if(tail){
      const wrap = document.createElement("div");
      wrap.innerHTML = renderMarkdown(tail);
      el.appendChild(wrap);
      wroteAny = true;
    }

    if(!wroteAny && !content.trim()){
      el.textContent = "";
    }
  }

  function renderMessageContent(el, text){
    const parsed = splitSuggestedText(text);
    el.innerHTML = "";
    if(parsed.body) renderTextWithImages(el, parsed.body);

    if(!parsed.queries.length) return;

    const wrap = document.createElement("div");
    wrap.className = "suggestions";
    parsed.queries.forEach(item => {
      const btn = document.createElement("button");
      btn.type = "button";
      btn.className = "suggestion-btn";
      btn.textContent = item.label || item.query;
      btn.addEventListener("click", () => sendMessage(item.query));
      wrap.appendChild(btn);
    });
    el.appendChild(wrap);
  }

  function extractRankChartData(text){
    const rows = [];
    const lines = (text || "").split(/\r?\n/);
    const rankRe = /^\s*(?:\d+\.\s+|\*\s+\d+\.\s+)(.+)$/;

    for(const line of lines){
      const rank = line.match(rankRe);
      if(!rank) continue;

      const raw = rank[1].trim();
      const score = raw.match(/\bscore\s+([\d.]+)/i);
      const revenue = raw.match(/\brevenue\s+\$?([\d,]+(?:\.\d+)?)/i);
      const qty = raw.match(/\bqty\s+([\d,]+(?:\.\d+)?)/i);
      const value = revenue ? Number(revenue[1].replace(/,/g, ""))
        : score ? Number(score[1])
        : qty ? Number(qty[1].replace(/,/g, ""))
        : 0;

      let label = raw.split(":")[0].trim();
      label = label.replace(/\s+/g, " ");
      if(label.length > 56) label = label.slice(0, 53) + "...";

      if(label && value > 0) rows.push({
        label,
        value,
        metric: revenue ? "revenue" : score ? "score" : "qty"
      });
    }

    if(rows.length) return rows.slice(0, 10);

    const tableRows = lines
      .map(line => line.trim())
      .filter(line => line.startsWith("|") && line.endsWith("|"))
      .map(line => line.slice(1, -1).split("|").map(cell => cell.trim()));

    if(tableRows.length >= 3){
      const headers = tableRows[0].map(h => h.toLowerCase());
      const dataRows = tableRows.slice(2);
      const valueIdx = headers.findIndex(h =>
        h.includes("revenue") || h.includes("amount") || h.includes("total") ||
        h.includes("qty") || h.includes("quantity") || h.includes("score")
      );
      const labelIdx = headers.findIndex(h =>
        h.includes("product") || h.includes("customer") || h.includes("category") ||
        h.includes("brand") || h.includes("code") || h.includes("name")
      );

      const metricHeader = headers[valueIdx] || "";
      const metric = metricHeader.includes("revenue") || metricHeader.includes("amount")
        ? "revenue" : metricHeader.includes("score") ? "score" : "qty";

      for(const cells of dataRows){
        if(!cells.length || cells.every(c => !c)) continue;
        const rawValue = cells[valueIdx >= 0 ? valueIdx : cells.length - 1] || "";
        const value = Number(rawValue.replace(/[^0-9.-]/g, ""));
        if(!Number.isFinite(value) || value <= 0) continue;

        let label = cells[labelIdx >= 0 ? labelIdx : 0] || cells.find(c => c && !/[0-9,.]+/.test(c)) || "Item";
        const productNameIdx = headers.findIndex(h => h === "product" || h.includes("product"));
        if(productNameIdx >= 0 && cells[productNameIdx]) label = cells[productNameIdx];
        if(label.length > 56) label = label.slice(0, 53) + "...";

        rows.push({label, value, metric});
      }
    }

    return rows.slice(0, 10);
  }

  function formatChartValue(item){
    if(item.metric === "revenue") return "$" + item.value.toLocaleString(undefined, {maximumFractionDigits: 0});
    if(item.metric === "score") return item.value.toLocaleString(undefined, {maximumFractionDigits: 2});
    return item.value.toLocaleString(undefined, {maximumFractionDigits: 0});
  }

  function renderRankChart(container, data, type="bar"){
    const chart = document.createElement("div");
    chart.className = "rank-chart";
    const max = Math.max(...data.map(x => x.value), 1);

    if(type === "column" || type === "line" || type === "pie"){
      renderSvgChart(chart, data, type, max);
      container.appendChild(chart);
      return;
    }

    data.forEach(item => {
      const row = document.createElement("div");
      row.className = "rank-chart-row";

      const label = document.createElement("div");
      label.className = "rank-chart-label";
      label.title = item.label;
      label.textContent = item.label;

      const track = document.createElement("div");
      track.className = "rank-chart-track";
      const bar = document.createElement("div");
      bar.className = "rank-chart-bar";
      bar.style.width = `${Math.max(3, (item.value / max) * 100)}%`;
      track.appendChild(bar);

      const value = document.createElement("div");
      value.className = "rank-chart-value";
      value.textContent = formatChartValue(item);

      row.appendChild(label); row.appendChild(track); row.appendChild(value);
      chart.appendChild(row);
    });

    container.appendChild(chart);
  }

  // URL params — optional overrides (avatar, modules passed from widget iframe)
  function renderSvgChart(chart, data, type, max){
    const w = 420, h = 190, pad = 24;
    const escapeSvg = s => String(s || "").replace(/[&<>"']/g, ch => ({
      "&":"&amp;", "<":"&lt;", ">":"&gt;", '"':"&quot;", "'":"&#39;"
    }[ch]));
    const short = s => {
      s = String(s || "");
      return s.length > 12 ? s.slice(0, 11) + "..." : s;
    };

    if(type === "pie"){
      const total = data.reduce((sum, item) => sum + item.value, 0) || 1;
      const colors = ["#1e3a6e", "#2f6f9f", "#5b8c5a", "#c0842f", "#8a5a9e", "#557aa8", "#9a6b43", "#6f7f9f"];
      let angle = -Math.PI / 2;
      const slices = data.slice(0, 8).map((item, i) => {
        const next = angle + (item.value / total) * Math.PI * 2;
        const large = next - angle > Math.PI ? 1 : 0;
        const x1 = 100 + 72 * Math.cos(angle), y1 = 88 + 72 * Math.sin(angle);
        const x2 = 100 + 72 * Math.cos(next),  y2 = 88 + 72 * Math.sin(next);
        angle = next;
        return `<path d="M100 88 L${x1.toFixed(2)} ${y1.toFixed(2)} A72 72 0 ${large} 1 ${x2.toFixed(2)} ${y2.toFixed(2)} Z" fill="${colors[i % colors.length]}"><title>${escapeSvg(item.label)}: ${escapeSvg(formatChartValue(item))}</title></path>`;
      }).join("");
      const legend = data.slice(0, 8).map((item, i) =>
        `<g transform="translate(205 ${24 + i * 18})"><rect width="9" height="9" fill="${colors[i % colors.length]}" rx="2"/><text x="14" y="9" font-size="10" fill="#1e3a6e">${escapeSvg(short(item.label))}</text></g>`
      ).join("");
      chart.innerHTML = `<svg viewBox="0 0 420 190" role="img">${slices}${legend}</svg>`;
      return;
    }

    const usableW = w - pad * 2;
    const usableH = h - pad * 2 - 18;
    const points = data.map((item, i) => {
      const x = pad + (data.length === 1 ? usableW / 2 : (i / (data.length - 1)) * usableW);
      const y = pad + usableH - (item.value / max) * usableH;
      return {x, y, item};
    });

    if(type === "line"){
      const path = points.map((p, i) => `${i ? "L" : "M"}${p.x.toFixed(2)} ${p.y.toFixed(2)}`).join(" ");
      const dots = points.map(p => `<circle cx="${p.x}" cy="${p.y}" r="3.5" fill="#1e3a6e"><title>${escapeSvg(p.item.label)}: ${escapeSvg(formatChartValue(p.item))}</title></circle>`).join("");
      const step = Math.max(1, Math.ceil(points.length / 5));
      const labels = points.map((p, i) => i % step === 0 ? `<text x="${p.x}" y="${h - 6}" text-anchor="middle" font-size="9" fill="#8a9bb5">${escapeSvg(short(p.item.label))}</text>` : "").join("");
      chart.innerHTML = `<svg viewBox="0 0 ${w} ${h}" role="img"><path d="${path}" fill="none" stroke="#1e3a6e" stroke-width="2.5"/>${dots}${labels}</svg>`;
      return;
    }

    const gap = 8;
    const barW = Math.max(10, (usableW - gap * (data.length - 1)) / data.length);
    const bars = data.map((item, i) => {
      const bh = Math.max(2, (item.value / max) * usableH);
      const x = pad + i * (barW + gap);
      const y = pad + usableH - bh;
      return `<rect x="${x}" y="${y}" width="${barW}" height="${bh}" rx="3" fill="#1e3a6e"><title>${escapeSvg(item.label)}: ${escapeSvg(formatChartValue(item))}</title></rect><text x="${x + barW / 2}" y="${h - 6}" text-anchor="middle" font-size="9" fill="#8a9bb5">${escapeSvg(short(item.label))}</text>`;
    }).join("");
    chart.innerHTML = `<svg viewBox="0 0 ${w} ${h}" role="img">${bars}</svg>`;
  }

  function renderChartSuggestion(row, suggestion, text){
    const data = extractRankChartData(text);
    if(!suggestion) return;

    const actions = document.createElement("div");
    actions.className = "chart-actions";

    const question = document.createElement("div");
    question.className = "chart-question";
    question.textContent = suggestion.question || "Would you like to display this as a chart?";
    actions.appendChild(question);

    const optionRow = document.createElement("div");
    optionRow.className = "chart-option-row";
    optionRow.style.display = "none";

    const showBtn = document.createElement("button");
    showBtn.type = "button";
    showBtn.className = "chart-toggle";
    showBtn.textContent = "Show chart options";
    showBtn.addEventListener("click", () => {
      showBtn.style.display = "none";
      optionRow.style.display = "flex";
      smoothScroll();
    });
    actions.appendChild(showBtn);
    actions.appendChild(optionRow);

    let chart = null, activeBtn = null;
    (suggestion.options || []).forEach(opt => {
      const btn = document.createElement("button");
      btn.type = "button";
      btn.className = "chart-toggle";
      btn.textContent = opt.label || opt.type || "Chart";
      btn.addEventListener("click", () => {
        if(chart) chart.remove();
        if(activeBtn) activeBtn.classList.remove("active");
        activeBtn = btn;
        activeBtn.classList.add("active");
        const wrap = document.createElement("div");
        if(data.length < 2){
          chart = document.createElement("div");
          chart.className = "rank-chart rank-chart-empty";
          chart.textContent = "I need at least two ranked rows to draw a chart.";
        }else{
          renderRankChart(wrap, data, opt.type || "bar");
          chart = wrap.firstElementChild;
        }
        actions.appendChild(chart);
        smoothScroll();
      });
      optionRow.appendChild(btn);
    });

    row.appendChild(actions);
  }

  function getParam(k,fb){ return new URLSearchParams(window.location.search).get(k)||fb; }
  function getAvatarUrl()  { return getParam("avatar_url",""); }
  function getModules()    {
    try{ const r=getParam("modules",""); return r?JSON.parse(decodeURIComponent(r)):null; }
    catch{ return null; }
  }

  //── DOM refs ─────────────────────────────────────────────────────────────────
  const msgEl   = document.getElementById("messages");
  const recentEl = document.getElementById("recent-list");
  const recentSearchEl = document.getElementById("recent-search");
  if(recentSearchEl){
    recentSearchEl.addEventListener("input", () => renderRecentChats(recentSearchEl.value));
  }
  const inputEl = document.getElementById("user-input");
  const sendBtn = document.getElementById("send-btn");
  let unreadCount = 0, isVisible = true;

  //── Widget bridge ─────────────────────────────────────────────────────────────
  function notifyUnread(n){ try{ if(window.parent?.updateAIBadge) window.parent.updateAIBadge(n); }catch(e){} }
  window.onChatOpened = function(){ isVisible=true; unreadCount=0; notifyUnread(0); smoothScroll(); };
  window.clearChatHistory = async function(){
    await callAjax("clear_history", {user_id: USER_ID, company_id: COMPANY_ID});
    setCurrentSession("");
    currentSessionMessages = [];
    currentSessionHasMore = false;
    currentSessionOldestId = null;
    msgEl.innerHTML=""; unreadCount=0; notifyUnread(0);
    addBotMessage("History cleared! How can I help you?",[],null);
  };

  //── Scroll ────────────────────────────────────────────────────────────────────
  let scrollRaf = null;
  function smoothScroll(){
    if(scrollRaf) cancelAnimationFrame(scrollRaf);
    scrollRaf = requestAnimationFrame(()=>{ msgEl.scrollTop = msgEl.scrollHeight; });
  }

  //── Helpers ───────────────────────────────────────────────────────────────────
  function formatTime(iso){ return iso?new Date(iso).toLocaleTimeString([],{hour:"2-digit",minute:"2-digit"}):""; }
  function formatDate(iso){ return iso?new Date(iso).toLocaleDateString([],{day:"2-digit",month:"short",year:"numeric"}):""; }
  function escHtml(t){ return(t||"").replace(/&/g,"&amp;").replace(/</g,"&lt;").replace(/>/g,"&gt;"); }

  //── Lightbox ──────────────────────────────────────────────────────────────────
  function openLightbox(src){ document.getElementById("lightbox-img").src=src; document.getElementById("lightbox").classList.add("open"); }
  function closeLightbox(){ document.getElementById("lightbox").classList.remove("open"); }
  document.getElementById("lightbox").addEventListener("click",function(e){ if(e.target===this)closeLightbox(); });

  //── Avatars ───────────────────────────────────────────────────────────────────
  function userAvatarHtml(){
    const url=getAvatarUrl(), init=USER_ID[0].toUpperCase();
    if(url) return `<div class="user-avatar"><img src="${url}" onerror="this.parentElement.textContent='${init}'"/></div>`;
    return `<div class="user-avatar">${init}</div>`;
  }

  //── Typewriter ────────────────────────────────────────────────────────────────
  const TW_SPEED = 16;

  function typewriter(el, text, onDone){
    el.innerHTML = "";
    const cursor = document.createElement("span");
    cursor.className = "tw-cursor";
    el.appendChild(cursor);
    const chars = [...text];
    let i = 0;
    const node = document.createTextNode("");
    el.insertBefore(node, cursor);
    function tick(){
      if(i >= chars.length){ cursor.remove(); if(onDone) onDone(); return; }
      node.textContent += chars[i++];
      smoothScroll();
      setTimeout(tick, TW_SPEED);
    }
    tick();
  }

  //── Static message helpers ────────────────────────────────────────────────────
  function addUserMessage(text, timestamp, scroll=true){
    const row=document.createElement("div"); row.className="msg-row user";
    const inner=document.createElement("div"); inner.className="msg-inner";
    inner.innerHTML=`${userAvatarHtml()}<div class="bubble">${escHtml(text)}</div>`;
    row.appendChild(inner);
    if(timestamp){ const t=document.createElement("div"); t.className="msg-time"; t.textContent=formatTime(timestamp); row.appendChild(t); }
    msgEl.appendChild(row);
    if(scroll) smoothScroll();
  }

  function addBotMessage(text, sources, timestamp, scroll=true){
    const row=document.createElement("div"); row.className="msg-row bot";
    const inner=document.createElement("div"); inner.className="msg-inner";
    const avatar=document.createElement("div"); avatar.className="bot-avatar"; avatar.innerHTML='<svg width="18" height="18" viewBox="0 0 32 32" fill="none" xmlns="http://www.w3.org/2000/svg"><rect width="32" height="32" rx="6" fill="#1a73e8"/><text x="16" y="22" text-anchor="middle" fill="white" font-size="18" font-weight="bold" font-family="Arial">AI</text></svg>';
    const bubble=document.createElement("div"); bubble.className="bubble";
    renderMessageContent(bubble, text);
    inner.appendChild(avatar); inner.appendChild(bubble);
    row.appendChild(inner);
    if(timestamp){ const t=document.createElement("div"); t.className="msg-time"; t.textContent=formatTime(timestamp); row.appendChild(t); }
    if(SHOW_SOURCES && sources?.length){ const s=document.createElement("div"); s.className="msg-sources"; s.innerHTML=`📄 <span>${sources.map(s=>s.split(/[\\/]/).pop()).join(", ")}</span>`; row.appendChild(s); }
    msgEl.appendChild(row);
    if(!isVisible&&scroll){ unreadCount++; notifyUnread(unreadCount); }
    if(scroll) smoothScroll();
  }

  //── Streaming bot row ─────────────────────────────────────────────────────────
  function createStreamingBotRow(){
    const row=document.createElement("div"); row.className="msg-row bot";
    const inner=document.createElement("div"); inner.className="msg-inner";
    const avatar=document.createElement("div"); avatar.className="bot-avatar"; avatar.innerHTML='<svg width="18" height="18" viewBox="0 0 32 32" fill="none" xmlns="http://www.w3.org/2000/svg"><rect width="32" height="32" rx="6" fill="#1a73e8"/><text x="16" y="22" text-anchor="middle" fill="white" font-size="18" font-weight="bold" font-family="Arial">AI</text></svg>';
    const bubble=document.createElement("div"); bubble.className="bubble";
    inner.appendChild(avatar); inner.appendChild(bubble); row.appendChild(inner);
    const timeEl=document.createElement("div"); timeEl.className="msg-time"; row.appendChild(timeEl);
    msgEl.appendChild(row);
    smoothScroll();

    let interDots=null;
    const stepBlocks=[];

    function appendImage(block, img){
      const url = resolveStepImageSrc(img);
      if(!url || !block || block.querySelector(".step-image")) return false;
      const wrap=document.createElement("div"); wrap.className="step-image";
      const imgEl=document.createElement("img");
      imgEl.src=url; imgEl.alt="illustration";
      imgEl.onclick=()=>openLightbox(url);
      imgEl.onerror=()=>{ wrap.style.display="none"; };
      wrap.appendChild(imgEl); block.appendChild(wrap); smoothScroll();
      return true;
    }

    return {
      row, bubble,

      showDots(){
        if(interDots) return;
        interDots=document.createElement("div"); interDots.className="inter-step-dots";
        interDots.innerHTML="<span></span><span></span><span></span>";
        bubble.appendChild(interDots); smoothScroll();
      },
      hideDots(){ if(interDots){ interDots.remove(); interDots=null; } },

      addIntro(text, onDone){
        const d=document.createElement("div"); d.className="response-intro";
        bubble.appendChild(d);
        typewriter(d, text, ()=>{
          renderMessageContent(d, text);  // re-render as markdown after typing
          if(onDone) onDone();
        });
      },

      addStep(text, img, isMulti, stepIndex, onDone){
        this.hideDots();
        const block=document.createElement("div"); block.className="step-block";
        const textEl=document.createElement("div"); textEl.className="step-text";
        block.appendChild(textEl); bubble.appendChild(block);
        stepBlocks[stepIndex] = block;
        typewriter(textEl, `${stepIndex+1}. `+text, ()=>{
          const shown = appendImage(block, img);
          if(shown){
            const imgEl = block.querySelector(".step-image img");
            if(imgEl){
              imgEl.onload=()=>{ smoothScroll(); if(onDone) setTimeout(onDone,200); };
              setTimeout(()=>{ if(onDone) onDone(); }, 2000);
              return;
            }
          }
          if(onDone) setTimeout(onDone,100);
        });
      },

      attachStepImage(stepNumber, img){
        const idx = Number(stepNumber || 0) - 1;
        const block = stepBlocks[idx];
        if(!block) return false;
        return appendImage(block, img);
      },

      addClosing(text){
        this.hideDots();
        const d=document.createElement("div"); d.className="step-block";
        d.style.cssText="margin-top:8px;padding-top:8px;border-top:1px solid #f0f0f0;";
        const inner=document.createElement("div"); inner.className="step-text";
        inner.style.cssText="color:#555;font-size:13px;";
        d.appendChild(inner); bubble.appendChild(d);
        typewriter(inner, text, ()=>{
          renderMessageContent(inner, text);
          smoothScroll();
        });
      },

      renumberAllSteps(total){
        if(total<=1) return;
        bubble.querySelectorAll(".step-block .step-text").forEach((el,i)=>{
          if(!el.dataset.numbered){ el.dataset.numbered="1"; const t=el.textContent; if(!t.match(/^\d+\. /)) el.textContent=`${i+1}. `+t; }
        });
      },

      finalize(sources, question, answer, timestamp, versionIds=[], chartSuggestion=null){
        this.hideDots();
        timeEl.textContent=formatTime(timestamp);
        if(SHOW_SOURCES && sources?.length){ const s=document.createElement("div"); s.className="msg-sources"; s.innerHTML=`📄 <span>${sources.map(s=>s.split(/[\\/]/).pop()).join(", ")}</span>`; row.appendChild(s); }
        if(chartSuggestion) renderChartSuggestion(row, chartSuggestion, answer);
        if(question&&answer){
          const ts=Date.now();
          const fbRow=document.createElement("div"); fbRow.className="feedback-row";
          fbRow.innerHTML=`<span>Helpful?</span><button class="fb-btn" id="fy-${ts}">👍 Yes</button><button class="fb-btn" id="fn-${ts}">👎 No</button>`;
          const yBtn=fbRow.querySelector(`#fy-${ts}`), nBtn=fbRow.querySelector(`#fn-${ts}`);

          const panel=document.createElement("div"); panel.className="fb-panel"; panel.style.display="none";
          panel.innerHTML=`
            <div class="fb-panel-title">What went wrong?</div>
            <div class="fb-reasons">
              <label class="fb-reason"><input type="radio" name="fbr-${ts}" value="wrong_answer"> Answer doesn't match my question</label>
              <label class="fb-reason"><input type="radio" name="fbr-${ts}" value="incomplete"> Answer is incomplete or missing steps</label>
              <label class="fb-reason"><input type="radio" name="fbr-${ts}" value="outdated"> Steps don't match the current system</label>
              <label class="fb-reason"><input type="radio" name="fbr-${ts}" value="too_complex"> Too complex or hard to follow</label>
              <label class="fb-reason"><input type="radio" name="fbr-${ts}" value="missing_images"> Missing screenshots</label>
              <label class="fb-reason"><input type="radio" name="fbr-${ts}" value="other"> Other</label>
            </div>
            <textarea class="fb-comment" rows="2" placeholder="Add a comment... (optional)"></textarea>
            <div class="fb-actions">
              <button class="fb-cancel" id="fbc-${ts}">Cancel</button>
              <button class="fb-submit" id="fbs-${ts}">Submit Feedback</button>
            </div>`;

          panel.querySelectorAll('.fb-reason input').forEach(r=>{
            r.addEventListener('change',()=>{
              panel.querySelectorAll('.fb-reason').forEach(l=>l.classList.remove('selected'));
              r.closest('.fb-reason').classList.add('selected');
            });
          });

          yBtn.addEventListener("click", async()=>{
            yBtn.classList.add("loading"); yBtn.innerHTML=`<span class="spinner"></span> Saving...`;
            nBtn.classList.add("dismissed"); panel.style.display="none";
            await saveFeedback(question,"up",versionIds,"","");
            yBtn.classList.remove("loading"); yBtn.className="fb-btn confirmed"; yBtn.textContent="✓ Thanks!";
          });

          nBtn.addEventListener("click",()=>{
            yBtn.classList.add("dismissed");
            nBtn.className="fb-btn confirmed"; nBtn.textContent="👎";
            panel.style.display="block"; smoothScroll();
          });

          panel.querySelector(`#fbc-${ts}`).addEventListener("click",()=>{
            panel.style.display="none";
            nBtn.className="fb-btn"; nBtn.textContent="👎 No";
            yBtn.classList.remove("dismissed");
          });

          panel.querySelector(`#fbs-${ts}`).addEventListener("click", async()=>{
            const selected=panel.querySelector(`input[name="fbr-${ts}"]:checked`);
            const reason  =selected?selected.value:"other";
            const comment =panel.querySelector(".fb-comment").value.trim();
            const submitBtn=panel.querySelector(`#fbs-${ts}`);
            submitBtn.disabled=true; submitBtn.innerHTML=`<span class="spinner"></span> Sending...`;
            const result=await saveFeedback(question,"down",versionIds,reason,comment);
            if(result?.preference_updated && result?.preference_change){
              const pref=result.preference_change;
              let msg="";
              if(pref.response_len==="detailed")      msg="Got it! I'll give more detailed answers from now on 😊";
              else if(pref.response_len==="short")     msg="Got it! I'll keep my answers more concise from now on 😊";
              else if(pref.language==="vi")             msg="Được rồi! Tôi sẽ trả lời bằng tiếng Việt từ bây giờ 😊";
              else if(pref.language==="en")             msg="Got it! I'll reply in English from now on 😊";
              if(msg){
                const toast=document.createElement("div");
                toast.style.cssText="font-size:12px;color:var(--clr-primary);margin-top:6px;padding:4px 0;";
                toast.textContent="✨ "+msg; panel.appendChild(toast);
              }
            }
            panel.querySelector(".fb-reasons").style.display="none";
            panel.querySelector(".fb-comment").style.display="none";
            panel.querySelector(".fb-actions").style.display="none";
            panel.querySelector(".fb-panel-title").textContent="✓ Thank you for your feedback!";
            panel.querySelector(".fb-panel-title").style.color="#34a853";
            setTimeout(()=>{ panel.style.display="none"; }, 2500);
          });

          row.appendChild(fbRow); row.appendChild(panel);
        }
        if(!isVisible){ unreadCount++; notifyUnread(unreadCount); }
        smoothScroll();
      }
    };
  }

  //── Typing indicator ──────────────────────────────────────────────────────────
  function addTypingIndicator(){
    const wrap=document.createElement("div"); wrap.className="typing-row";
    wrap.innerHTML=`<div class="bot-avatar"><svg width="18" height="18" viewBox="0 0 32 32" fill="none" xmlns="http://www.w3.org/2000/svg"><rect width="32" height="32" rx="6" fill="#1a73e8"/><text x="16" y="22" text-anchor="middle" fill="white" font-size="18" font-weight="bold" font-family="Arial">AI</text></svg></div>
      <div class="typing-content">
        <div class="typing-dots"><span></span><span></span><span></span></div>
        <div class="typing-status">Connecting...</div>
      </div>`;
    msgEl.appendChild(wrap); smoothScroll();
    const statusEl=wrap.querySelector(".typing-status");
    return {
      remove(){ wrap.remove(); },
      setStatus(text){ statusEl.classList.add("fade"); setTimeout(()=>{ statusEl.textContent=text; statusEl.classList.remove("fade"); },250); }
    };
  }

  //── History ───────────────────────────────────────────────────────────────────
  async function loadHistory(){
    const loadEl=document.getElementById("history-loading");
    try{
      const res=await callAjax("get_sessions", {user_id:USER_ID, company_id:COMPANY_ID}, 6000);
      if(!res.ok) throw new Error(`HTTP ${res.status}`);
      const data=await res.json();
      const sessions = data.sessions || [];
      buildRecentChats(sessions);
      loadEl.style.display="none";
      const savedSession = (() => { try { return localStorage.getItem(SESSION_KEY) || ""; } catch(e) { return ""; } })();
      const initialSession = sessions.find(s => s.session_id === savedSession) || sessions[0];
      if(initialSession){
        await openRecentChat(initialSession.session_id);
      } else {
        setCurrentSession("");
        updateSessionStrip(0);
        msgEl.innerHTML = "";
        addBotMessage(`Hi ${displayUserName()}! I'm your ERP Assistant. How can I help you today?`,[],new Date().toISOString());
      }
    }catch(e){
      loadEl.style.display="none";
      updateSessionStrip(0);
      addBotMessage(`Hi ${displayUserName()}! I'm your ERP Assistant. How can I help you today?`,[],new Date().toISOString());
    }
  }

  async function loadAIGreeting(){
    const typing=addTypingIndicator(); typing.setStatus("Loading your conversation...");
    try{
      const res=await callAjax("chat_greeting", {user_id:USER_ID, company_id:COMPANY_ID, modules: JSON.stringify(getModules())}, 5000);
      if(!res.ok) throw new Error(`HTTP ${res.status}`);
      const data=await res.json(); typing.remove();
      const baseMsg = (data.message || data.greeting || "How can I help you today?").trim();
      const msg = `Welcome back ${displayUserName()}! ${baseMsg.replace(/^hello again[!,.]?\s*/i, "")}`;
      addBotMessage(msg,[],new Date().toISOString()); smoothScroll();
    }catch(e){ typing.remove(); addBotMessage(`Welcome back ${displayUserName()}! How can I help you today?`,[],new Date().toISOString()); }
  }

  loadHistory();

  //── Input handlers ────────────────────────────────────────────────────────────
  inputEl.addEventListener("input",()=>{ inputEl.style.height="auto"; inputEl.style.height=inputEl.scrollHeight+"px"; });
  inputEl.addEventListener("keydown",e=>{ if(e.key==="Enter"&&!e.shiftKey){ e.preventDefault(); sendMessage(); } });
  sendBtn.addEventListener("click",sendMessage);
  document.addEventListener("visibilitychange",()=>{ isVisible=!document.hidden; if(isVisible){ unreadCount=0; notifyUnread(0); } });

  //── Send message ──────────────────────────────────────────────────────────────
  async function sendMessage(prefillText){
    const text=(typeof prefillText === "string" ? prefillText : inputEl.value).trim(); if(!text) return;
    if(!currentSessionId) setCurrentSession(getNewSessionId());
    addUserMessage(text,new Date().toISOString());
    const existingSession = recentChats.find(item => item.id === currentSessionId);
    if(existingSession){
      existingSession.title = shortenTitle(existingSession.full || text);
      existingSession.full = existingSession.full || text;
      existingSession.msgCount = Math.max(Number(existingSession.msgCount || 0), currentSessionMessages.length + 1);
    } else {
      recentChats.unshift({
        id: currentSessionId,
        sessionId: currentSessionId,
        title: shortenTitle(text),
        full: text,
        messages: [],
        msgCount: 1,
        createdAt: new Date().toISOString(),
        updatedAt: new Date().toISOString(),
        firstUserMsg: text
      });
    }
    recentChats = recentChats.slice(0, 18);
    renderRecentChats(recentSearchEl ? recentSearchEl.value : "");
    inputEl.value=""; inputEl.style.height="auto"; sendBtn.disabled=true;

    const typing=addTypingIndicator();
    let streamRow=null, allSteps=[], sources=[], versionIds=[], receivedDone=false, introText="", chartSuggestion=null;

    // Step queue — process one step at a time for sequential typewriter effect
    const queue=[]; let queueRunning=false, pendingClosing=null;
    const pendingStepImages = new Map();

    function consumePendingStepImage(stepNumber, obj){
      const key = Number(stepNumber || 0);
      if(!key || !pendingStepImages.has(key) || (obj && obj.image)) return obj;
      const nextObj = obj || {};
      nextObj.image = pendingStepImages.get(key);
      pendingStepImages.delete(key);
      return nextObj;
    }

    function tryRenderClosing(){
      if(!pendingClosing||!streamRow) return;
      if(queueRunning||queue.length>0){ setTimeout(tryRenderClosing,150); return; }
      streamRow.addClosing(pendingClosing); pendingClosing=null;
    }

    function processQueue(){
      if(queue.length===0){
        queueRunning=false;
        if(streamRow&&!receivedDone) streamRow.showDots();
        tryRenderClosing(); return;
      }
      queueRunning=true;
      const queued = queue.shift();
      const stepObj = consumePendingStepImage(queued?.step_number, queued);
      const stepIndex=allSteps.length; allSteps.push(stepObj);
      streamRow.addStep(stepObj.text,stepObj.image,true,stepIndex,()=>{ processQueue(); });
    }

    function enqueueStep(obj){
      queue.push(consumePendingStepImage(obj?.step_number, obj));
      if(!queueRunning) processQueue();
    }

    function syncCurrentSession(answerText){
      const ts = new Date().toISOString();
      currentSessionMessages = currentSessionMessages.concat([
        {role:"user", content:text, timestamp:ts},
        {role:"assistant", content:answerText, timestamp:ts}
      ]);
      updateSessionStrip(currentSessionMessages.length);
      const sessionItem = recentChats.find(item => item.id === currentSessionId);
      if(sessionItem){
        sessionItem.messages = currentSessionMessages.slice();
        sessionItem.msgCount = currentSessionMessages.length;
        sessionItem.updatedAt = ts;
        sessionItem.hasMore = currentSessionHasMore;
        sessionItem.oldestId = currentSessionOldestId;
        sessionItem._loadedAt = ts;
        sessionItem._cachedHtml = "";
      }
    }

    try{
      const streamBody=new URLSearchParams({action:"chat_stream",user_id:USER_ID,company_id:COMPANY_ID,masterfn:MASTERFN,companyfn:COMPANYFN,lang:LANG,query:text,session_id:currentSessionId});
      const res=await fetch(AJAX_URL,{method:"POST",headers:{"Content-Type":"application/x-www-form-urlencoded"},body:streamBody.toString()});
      if(!res.ok) throw new Error(`HTTP ${res.status}`);

      const reader=res.body.getReader(), decoder=new TextDecoder();
      let buf="", evType="";

      while(true){
        const {done,value}=await reader.read(); if(done) break;
        buf+=decoder.decode(value,{stream:true});
        const lines=buf.split("\n"); buf=lines.pop();

        for(const line of lines){
          if(line.startsWith("event: ")){ evType=line.slice(7).trim(); continue; }
          if(!line.startsWith("data: ")) continue;
          const ds=line.slice(6).trim(); if(!ds) continue;
          try{
            const obj=JSON.parse(ds);
            if(evType==="status"){
              typing.setStatus(obj.text);
            }else if(evType==="intro"){
              typing.remove(); streamRow=createStreamingBotRow();
              if(obj.text){ introText=obj.text; streamRow.addIntro(obj.text,()=>{ if(!receivedDone) streamRow.showDots(); }); }
            }else if(evType==="step"){
              if(!streamRow){ typing.remove(); streamRow=createStreamingBotRow(); }
              streamRow.hideDots();
              enqueueStep({
                step_number: obj.step_number,
                text: obj.text,
                image: obj.image || obj.image_keyword || null
              });
            }else if(evType==="image"){
              const imgData = obj.image ? `data:image/png;base64,${obj.image}` : null;
              if(imgData && typeof obj.step !== "undefined"){
                pendingStepImages.set(Number(obj.step), imgData);
                if(streamRow) streamRow.attachStepImage(obj.step, imgData);
              }
            }else if(evType==="total"){
              if(streamRow&&obj.total>1) streamRow.renumberAllSteps(obj.total);
            }else if(evType==="closing"){
              pendingClosing=obj.text; tryRenderClosing();
            }else if(evType==="meta"){
              sources=obj.sources||[]; versionIds=obj.version_ids||[];
            }else if(evType==="chart_suggestion"){
              chartSuggestion=obj;
            }else if(evType==="done"){
              receivedDone=true;
              function tryFinalize(){
                if(queueRunning||queue.length>0){ setTimeout(tryFinalize,100); return; }
                if(!streamRow){
                  typing.remove();
                  addBotMessage("⚠️ I could not generate an answer for that request. Please try rephrasing it or check that the ERP data service is running.",[],new Date().toISOString());
                  return;
                }
                // Use introText as answer when no steps (e.g. data_query path)
                const plain=allSteps.length>0
                  ?allSteps.map((s,i)=>allSteps.length>1?`${i+1}. ${s.text}`:s.text).join("\n")
                  :introText;
                streamRow.finalize(sources,text,plain,new Date().toISOString(),versionIds,chartSuggestion);
                syncCurrentSession(plain);
              }
              tryFinalize();
            }
          }catch(e){}
        }
      }

      if(!receivedDone){
        if(streamRow){
          const plain=allSteps.length>0
            ?allSteps.map((s,i)=>allSteps.length>1?`${i+1}. ${s.text}`:s.text).join("\n")
            :introText;
          try{
            streamRow.finalize(sources,text,plain,new Date().toISOString(),versionIds,chartSuggestion);
          }catch(finalizeErr){
            console.error("Finalize fallback failed:", finalizeErr);
          }
        }else{
          typing.remove();
          addBotMessage("⚠️ I could not generate an answer for that request. Please try rephrasing it or check that the ERP data service is running.",[],new Date().toISOString());
        }
      }
    }catch(err){
      console.error("Chat stream error:", err);
      typing.remove();
      if(!streamRow){
        addBotMessage("⚠️ Cannot connect to AI server. Make sure the API is running.",[],null);
      }
    }
    sendBtn.disabled=false; inputEl.focus();
  }

  //── Feedback ──────────────────────────────────────────────────────────────────
  async function saveFeedback(question, rating="up", versionIds=[], reason="", comment=""){
    const body={user_id:USER_ID,company_id:COMPANY_ID,rating,
      reason:reason||"",comment:comment||"",query_text:question||""};
    let result=null;
    if(versionIds.length){
      for(const vid of versionIds){
        try{ const r=await callAjax("feedback",{...body,entry_version_id:vid}); if(r.ok&&!result) result=await r.json(); }catch(e){}
      }
    }else{
      try{ const r=await callAjax("feedback",body); if(r.ok) result=await r.json(); }catch(e){}
    }
    return result;
  }
</script>
</body>
</html>
