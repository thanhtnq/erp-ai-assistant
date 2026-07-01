<!---@ ###########################################################################################################
Version 5.0.1
File Description:
No	Modified Date	Modified By		Change Log
1.	20240701	Lopper		Creation Of File 
################################################################################################################# @--->
<cfparam name="cookie.cookuserloginid" default="user_001">
<cfparam name="cookie.cookmfnunique"   default="demo2011mfn">
<cfparam name="cookie.cookcfnunique"   default="p11011004464072155">

<cfset userModulesJSON = '["sales","purchase","crm","stock","finance","hr","project","general"]'>
<cfif isDefined("session.modules") AND isJSON(session.modules)>
  <cfset userModulesJSON = session.modules>
</cfif>

<style>
  :root {
    --ai-g3-primary: #002b63;
    --ai-g3-primary-soft: #1e5f9f;
    --ai-g3-bg: #eaeff7;
    --ai-g3-panel: #ffffff;
    --ai-g3-line: #d8e1f1;
    --ai-g3-muted: #6f829f;
    --ai-g3-shadow: 0 8px 24px rgba(0, 43, 99, 0.16);
    --ai-g3-font: 'Century Gothic', CenturyGothic, AppleGothic, sans-serif;
  }

  #ai-chat-btn {
    position: fixed;
    right: 22px;
    bottom: 18px;
    z-index: 99999;
    min-width: 132px;
    height: 42px;
    padding: 0 13px;
    display: inline-flex;
    align-items: center;
    justify-content: center;
    gap: 9px;
    background: var(--ai-g3-panel);
    color: var(--ai-g3-primary);
    border: 1px solid #9db2d1;
    border-radius: 8px;
    box-shadow: 0 3px 10px rgba(0, 43, 99, 0.12);
    cursor: pointer;
    font-family: var(--ai-g3-font);
    font-size: 12px;
    font-weight: 700;
    letter-spacing: 0.06em;
    transition: background 0.15s, border-color 0.15s, box-shadow 0.15s;
  }

  #ai-chat-btn:hover {
    background: #f7faff;
    border-color: var(--ai-g3-primary);
    box-shadow: 0 5px 14px rgba(0, 43, 99, 0.16);
  }

  #ai-chat-btn img {
    width: 24px;
    height: 24px;
    object-fit: contain;
    display: block;
  }

  #ai-chat-btn .ai-chat-btn-label {
    white-space: nowrap;
  }

  #ai-unread-badge {
    position: fixed;
    right: 14px;
    bottom: 53px;
    z-index: 100000;
    min-width: 20px;
    height: 20px;
    padding: 0 5px;
    display: none;
    align-items: center;
    justify-content: center;
    background: #e53935;
    color: #ffffff;
    border: 2px solid #ffffff;
    border-radius: 10px;
    font-family: var(--ai-g3-font);
    font-size: 11px;
    font-weight: 700;
    animation: aiBadgePop 0.3s ease;
  }

  @keyframes aiBadgePop {
    0% { transform: scale(0); }
    70% { transform: scale(1.2); }
    100% { transform: scale(1); }
  }

  #ai-chat-wrapper {
    position: fixed;
    right: 22px;
    bottom: 72px;
    z-index: 99998;
    width: 600px;
    height: 620px;
    display: none;
    flex-direction: column;
    overflow: hidden;
    background: var(--ai-g3-panel);
    border: 1px solid #b9c8de;
    border-radius: 8px;
    box-shadow: var(--ai-g3-shadow);
    transition: width 0.2s, height 0.2s;
  }

  #ai-chat-wrapper.fullscreen {
    width: 860px;
    height: 82vh;
  }

  #ai-chat-header {
    min-height: 44px;
    padding: 7px 10px;
    display: flex;
    align-items: center;
    gap: 9px;
    flex-shrink: 0;
    background: #f8fbff;
    border-bottom: 1px solid var(--ai-g3-line);
  }

  #ai-chat-header .ai-avatar {
    width: 28px;
    height: 28px;
    display: flex;
    align-items: center;
    justify-content: center;
    background: #ffffff;
    border: 1px solid #c7d5e8;
    border-radius: 6px;
  }

  #ai-chat-header .ai-avatar img {
    width: 21px;
    height: 21px;
    object-fit: contain;
    display: block;
  }

  #ai-chat-header .ai-info h3 {
    margin: 0;
    color: var(--ai-g3-primary);
    font-family: var(--ai-g3-font);
    font-size: 12px;
    font-weight: 700;
    letter-spacing: 0.08em;
    line-height: 1.15;
  }

  #ai-chat-header .ai-info p {
    margin: 2px 0 0;
    color: var(--ai-g3-muted);
    font-family: var(--ai-g3-font);
    font-size: 10px;
    letter-spacing: 0.03em;
  }

  #ai-chat-header .ai-btns {
    margin-left: auto;
    display: flex;
    gap: 6px;
  }

  #ai-chat-header .ai-btns button {
    min-width: 28px;
    height: 26px;
    padding: 0 8px;
    display: inline-flex;
    align-items: center;
    justify-content: center;
    background: #ffffff;
    color: var(--ai-g3-primary);
    border: 1px solid #c7d5e8;
    border-radius: 6px;
    cursor: pointer;
    font-family: var(--ai-g3-font);
    font-size: 11px;
    white-space: nowrap;
  }

  #ai-chat-header .ai-btns button:hover {
    background: #eaf1fb;
    border-color: var(--ai-g3-primary);
  }

  #ai-chat-frame {
    flex: 1;
    width: 100%;
    border: none;
    background: var(--ai-g3-bg);
  }

  @media (max-width: 520px) {
    #ai-chat-wrapper {
      left: 8px;
      right: 8px;
      bottom: 66px;
      width: auto;
      height: min(620px, calc(100vh - 82px));
    }

    #ai-chat-wrapper.fullscreen {
      left: 8px;
      right: 8px;
      width: auto;
      height: calc(100vh - 82px);
    }

    #ai-chat-btn {
      right: 12px;
      bottom: 12px;
      min-width: 116px;
      height: 40px;
    }
  }

  /* Large ERP desktop size: make both normal and expanded modes readable. */
  @media (min-width: 900px) {
    #ai-chat-wrapper {
      width: 1100px;
      height: 760px;
      right: 24px;
      bottom: 76px;
    }

    #ai-chat-wrapper.fullscreen {
      width: calc(100vw - 80px);
      height: calc(100vh - 110px);
      right: 40px;
      bottom: 70px;
    }

    #ai-chat-header {
      min-height: 66px;
      padding: 10px 14px;
      gap: 12px;
    }

    #ai-chat-header .ai-avatar {
      width: 42px;
      height: 42px;
    }

    #ai-chat-header .ai-avatar img {
      width: 31px;
      height: 31px;
    }

    #ai-chat-header .ai-info h3 {
      font-size: 18px;
    }

    #ai-chat-header .ai-info p {
      font-size: 13px;
    }

    #ai-chat-header .ai-btns button {
      min-width: 44px;
      height: 38px;
      padding: 0 13px;
      font-size: 15px;
    }
  }
</style>

<div id="ai-unread-badge">0</div>
<button id="ai-chat-btn" onclick="toggleAIChat()" title="ERP Assistant">
  <img src="logo.png" alt="ERP Assistant">
  <span class="ai-chat-btn-label">AI CHATBOX</span>
</button>

<div id="ai-chat-wrapper">
  <div id="ai-chat-header">
    <div class="ai-avatar">
      <img src="logo.png" alt="ERP Assistant">
    </div>
    <div class="ai-info">
      <h3>ERP Assistant</h3>
      <p>AI - User Manual</p>
    </div>
    <div class="ai-btns">
      <button onclick="clearAIChat()" title="Clear history">Clear</button>
      <button onclick="resizeAIChat()" id="ai-resize-btn" title="Expand">[]</button>
      <button onclick="toggleAIChat()" title="Close">X</button>
    </div>
  </div>
  <cfoutput>
  <iframe id="ai-chat-frame"
    src="ai_assistant.cfm?modules=#URLEncodedFormat(userModulesJSON)#">
  </iframe>
  </cfoutput>
</div>

<script>
  var aiChatOpen   = false;
  var aiFullscreen = false;

  function updateAIBadge(count){
    var badge=document.getElementById("ai-unread-badge");
    if(count>0 && !aiChatOpen){ badge.textContent=count>99?"99+":count; badge.style.display="flex"; }
    else{ badge.style.display="none"; }
  }

  function toggleAIChat(){
    var wrapper=document.getElementById("ai-chat-wrapper");
    var btn=document.getElementById("ai-chat-btn");
    aiChatOpen=!aiChatOpen;
    wrapper.style.display=aiChatOpen?"flex":"none";
    btn.innerHTML=aiChatOpen
      ?'<span style="font-size:18px;color:#002b63;font-weight:700;line-height:1;">X</span><span class="ai-chat-btn-label">CLOSE</span>'
      :'<img src="logo.png" alt="ERP Assistant"><span class="ai-chat-btn-label">AI CHATBOX</span>';
    if(aiChatOpen){
      document.getElementById("ai-unread-badge").style.display="none";
      var frame=document.getElementById("ai-chat-frame");
      if(frame && frame.contentWindow && frame.contentWindow.onChatOpened) frame.contentWindow.onChatOpened();
    }
  }

  function resizeAIChat(){
    var wrapper=document.getElementById("ai-chat-wrapper");
    var btn=document.getElementById("ai-resize-btn");
    aiFullscreen=!aiFullscreen;
    wrapper.classList.toggle("fullscreen",aiFullscreen);
    btn.textContent=aiFullscreen?"--":"[]";
    btn.title=aiFullscreen?"Collapse":"Expand";
  }

  function clearAIChat(){
    var frame=document.getElementById("ai-chat-frame");
    if(frame && frame.contentWindow && frame.contentWindow.clearChatHistory) frame.contentWindow.clearChatHistory();
  }
</script>
