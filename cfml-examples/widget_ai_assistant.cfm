<!---
  ERP AI Assistant Widget
  Embed before </body> (or </frameset>) in the outermost ERP layout file.

  Reads from cookies:
    cookie.cookuserloginid  — current user ID
    cookie.cookmfnunique    — masterfn (client scope)
    cookie.cookcfnunique    — companyfn (entity scope)
    cookie.cooklang         — UI language ("english" / "vietnamese")

  Optional: override allowed modules via session.modules (JSON array).
--->

<cfparam name="cookie.cookuserloginid" default="user_001">
<cfparam name="cookie.cookmfnunique"   default="demo2011mfn">

<cfset userModulesJSON = '["sales","purchase","crm","stock","finance","hr","project","general"]'>
<cfif isDefined("session.modules") AND isJSON(session.modules)>
  <cfset userModulesJSON = session.modules>
</cfif>

<style>
  #ai-chat-btn {
    position: fixed; bottom: 20px; right: 20px;
    width: 72px; height: 72px; background: none;
    border: none; cursor: pointer; padding: 0;
    z-index: 99999; transition: transform 0.2s;
  }
  #ai-chat-btn:hover { transform: scale(1.1); }

  #ai-unread-badge {
    position: fixed; bottom: 82px; right: 14px;
    min-width: 20px; height: 20px; background: #e53935;
    border-radius: 10px; color: white; font-size: 11px; font-weight: bold;
    display: none; align-items: center; justify-content: center; padding: 0 5px;
    z-index: 100000; border: 2px solid white;
    font-family: 'Century Gothic', CenturyGothic, AppleGothic, sans-serif; animation: pop 0.3s ease;
  }
  @keyframes pop { 0%{transform:scale(0)} 70%{transform:scale(1.2)} 100%{transform:scale(1)} }

  #ai-chat-wrapper {
    position: fixed; bottom: 104px; right: 20px;
    z-index: 99998; display: none; flex-direction: column;
    border-radius: 12px; overflow: hidden;
    border: 1px solid #d0d9ea;
    box-shadow: 0 8px 32px rgba(30,58,110,0.18);
    width: 400px; height: 580px;
    transition: width 0.25s, height 0.25s;
  }
  #ai-chat-wrapper.fullscreen { width: 720px; height: 82vh; }

  #ai-chat-header {
    background: #1e3a6e; padding: 10px 14px;
    display: flex; align-items: center; gap: 10px; flex-shrink: 0;
  }
  #ai-chat-header .ai-avatar { font-size: 20px; }
  #ai-chat-header .ai-info h3 {
    color: white; font-size: 14px; font-weight: 600; margin: 0;
    font-family: system-ui, 'Segoe UI', Arial, sans-serif;
  }
  #ai-chat-header .ai-info p {
    color: rgba(255,255,255,0.85); font-size: 11px; margin: 1px 0 0;
    font-family: system-ui, 'Segoe UI', Arial, sans-serif;
  }
  #ai-chat-header .ai-btns { margin-left: auto; display: flex; gap: 6px; }
  #ai-chat-header .ai-btns button {
    background: rgba(255,255,255,0.2); border: none; color: white;
    border-radius: 6px; padding: 4px 9px; cursor: pointer;
    font-size: 12px; font-family: system-ui, 'Segoe UI', Arial, sans-serif; white-space: nowrap;
  }
  #ai-chat-header .ai-btns button:hover { background: rgba(255,255,255,0.35); }

  #ai-chat-frame { flex: 1; border: none; width: 100%; }
</style>

<div id="ai-unread-badge">0</div>
<button id="ai-chat-btn" onclick="toggleAIChat()" title="ERP Assistant">
  <img src="logo.png" alt="ERP Assistant" style="width:72px;height:72px;object-fit:contain;display:block;">
</button>

<div id="ai-chat-wrapper">
  <div id="ai-chat-header">
    <div class="ai-avatar">
      <img src="logo.png" alt="ERP Assistant" style="width:32px;height:32px;object-fit:contain;display:block;">
    </div>
    <div class="ai-info">
      <h3>ERP Assistant</h3>
      <p>AI · User Manual</p>
    </div>
    <div class="ai-btns">
      <button onclick="clearAIChat()" title="Clear history">🗑 Clear</button>
      <button onclick="resizeAIChat()" id="ai-resize-btn" title="Expand">⛶</button>
      <button onclick="toggleAIChat()" title="Close">✕</button>
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
      ?'<span style="font-size:22px;color:#1e3a6e;font-weight:700;line-height:1;">✕</span>'
      :'<img src="logo.png" alt="ERP Assistant" style="width:72px;height:72px;object-fit:contain;display:block;">';
    if(aiChatOpen){
      document.getElementById("ai-unread-badge").style.display="none";
      var frame=document.getElementById("ai-chat-frame");
      if(frame?.contentWindow?.onChatOpened) frame.contentWindow.onChatOpened();
    }
  }

  function resizeAIChat(){
    var wrapper=document.getElementById("ai-chat-wrapper");
    var btn=document.getElementById("ai-resize-btn");
    aiFullscreen=!aiFullscreen;
    wrapper.classList.toggle("fullscreen",aiFullscreen);
    btn.textContent=aiFullscreen?"⊡":"⛶";
    btn.title=aiFullscreen?"Collapse":"Expand";
  }

  function clearAIChat(){
    var frame=document.getElementById("ai-chat-frame");
    if(frame?.contentWindow?.clearChatHistory) frame.contentWindow.clearChatHistory();
  }
</script>
