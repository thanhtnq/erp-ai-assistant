
  //â”€â”€ Config â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
  // KhÃ´ng gá»i tháº³ng ra AI API ngoÃ i ná»¯a. Má»i request Ä‘i qua inc_ajax_ai_assistant.cfm (cÃ¹ng thÆ° má»¥c),
  // theo Ä‘Ãºng cáº¥u trÃºc inc_ajax_xxx.cfm (action + cfswitch) Ä‘ang dÃ¹ng trong há»‡ thá»‘ng.
  // File proxy giá»¯ API key á»Ÿ server nÃªn key khÃ´ng bao giá» lá»™ ra client/View Source.
  const AJAX_URL      = "inc_ajax_ai_assistant.cfm";
  const SHOW_SOURCES  = false;

  // Helper: gá»i 1 "action" trong inc_ajax_ai_assistant.cfm, body dáº¡ng form-urlencoded (chuáº©n cfparam)
  function callAjax(action, params={}, timeoutMs=7000){
    const body = new URLSearchParams({action, ...params});
    return fetchWithTimeout(AJAX_URL, {
      method: "POST",
      headers: {"Content-Type": "application/x-www-form-urlencoded"},
      body: body.toString()
    }, timeoutMs);
  }

  // Helper: build URL GET cho áº£nh (dÃ¹ng trong <img src>, khÃ´ng thá»ƒ POST Ä‘Æ°á»£c)
  function ajaxImageUrl(imagePath){
    return `${AJAX_URL}?action=get_image&image_path=${encodeURIComponent(imagePath)}`;
  }

  //â”€â”€ ERP session â€” injected server-side from cookies â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
  const USER_ID="test"; const COMPANY_ID="test"; const MASTERFN="m"; const COMPANYFN="c"; const LANG="english";

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
    const currentTitle = label.textContent.replace(/^ðŸ“Œ\s*/, "").trim();
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
      lastChartContext = null;
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
      lastChartContext = null;
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
        toast.textContent = "âœ“ Copied to clipboard!";
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
      const pinIndicator = isPinned ? '<span class="chat-pin-indicator">ðŸ“Œ</span>' : '';
      return `
        <div class="chat-item-wrap${isActive ? " active" : ""}${isPinned ? " pinned" : ""}" id="wrap-${item.id}" data-chat-id="${item.id}">
          <span class="chat-item-label" title="${escHtml(item.full)}">${pinIndicator}${escHtml(item.title)}</span>
          <div class="chat-item-actions">
            <button class="chat-menu-btn" data-action="menu" title="More">â‹®</button>
          </div>
          <div class="chat-dropdown" id="dd-${item.id}">
            <button class="chat-dropdown-item" data-action="share"><span class="dd-icon">â†—</span> Share</button>
            <div class="chat-dropdown-divider"></div>
            <button class="chat-dropdown-item danger" data-action="delete"><span class="dd-icon">Ã—</span> Delete</button>
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
    lastChartContext = null;
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


  // Render markdown safely â€” falls back to escaped text if marked.js unavailable
  function normalizeAssistantText(text){
    let t = String(text || "").replace(/\r\n/g, "\n");
    if(/\[(SCM Overview|Demand Forecast|Product Trend|Sales Forecast)\]/i.test(t)){
      t = t
        .replace(/^\s*-\s+/gm, "")
        .replace(/^\s*â€¢\s+/gm, "")
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
    if(renderStructuredChart(el, text)) return;
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
      const rawLabel = item.label || item.query;
      const iconMatch = String(rawLabel).match(/^([^\w\s])\s*(.+)$/);
      if(iconMatch){
        const ico = document.createElement("span");
        ico.className = "suggestion-ico";
        ico.textContent = iconMatch[1];
        const label = document.createElement("span");
        label.className = "suggestion-label";
        label.textContent = iconMatch[2];
        btn.appendChild(ico);
        btn.appendChild(label);
      }else{
        const ico = document.createElement("span");
        ico.className = "suggestion-ico";
        ico.textContent = "â€º";
        const label = document.createElement("span");
        label.className = "suggestion-label";
        label.textContent = rawLabel;
        btn.appendChild(ico);
        btn.appendChild(label);
      }
      btn.title = item.query;
      btn.addEventListener("click", () => sendMessage(item.query));
      wrap.appendChild(btn);
    });
    el.appendChild(wrap);
  }

  function parseStructuredChart(text){
    const raw = String(text || "").trim();
    if(!raw) return null;
    const block = raw.match(/```(?:g3chart|json)?\s*([\s\S]*?)```/i);
    let candidate = block ? block[1].trim() : raw;
    if(!/^\s*\{[\s\S]*\}\s*$/.test(candidate)){
      const start = candidate.indexOf("{");
      const end = candidate.lastIndexOf("}");
      if(start < 0 || end <= start) return null;
      candidate = candidate.slice(start, end + 1);
    }
    try{
      const cfg = JSON.parse(candidate);
      if(!cfg) return null;
      const firstSeries = Array.isArray(cfg.series) ? cfg.series[0] : null;
      const sourceRows = Array.isArray(cfg.data) ? cfg.data : Array.isArray(firstSeries?.data) ? firstSeries.data : [];
      if(!Array.isArray(sourceRows) || !sourceRows.length) return null;
      const labelField = firstSeries?.label_field || cfg.label_field || cfg.x_field || "";
      const valueField = firstSeries?.value_field || cfg.value_field || cfg.y_field || "";
      const rows = sourceRows.map(item => {
        const label = (labelField && item[labelField]) || item.label || item.name || item.customer || item.product || item.x || item.category || item.document || item.document_no || item["Document No."] || item["Sales Order"];
        const rawValue = (valueField && item[valueField]) ?? item.value ?? item.amount ?? item.total ?? item.y ?? item.sales ?? item.revenue ?? item.qty ?? item.quantity ?? item["Amount (Local)"] ?? item["Amount Local"];
        const value = Number(String(rawValue ?? "").replace(/[^0-9.-]/g, ""));
        if(!label || !Number.isFinite(value) || value <= 0) return null;
        const metric = /amount|sales|revenue|total/i.test([valueField, Object.keys(item).join(" ")].join(" ")) ? "revenue" : "qty";
        return {label:String(label), value, metric};
      }).filter(Boolean).slice(0, 10);
      if(rows.length < 2) return null;
      return {type: cfg.type || "bar", title: cfg.title || "", data: rows};
    }catch(e){
      return null;
    }
  }

  function renderStructuredChart(el, text){
    const cfg = parseStructuredChart(text);
    if(!cfg) return false;
    el.innerHTML = "";
    const intro = document.createElement("div");
    intro.textContent = cfg.title || "Here is the chart.";
    el.appendChild(intro);
    renderRankChart(el, cfg.data, cfg.type || "bar");
    return true;
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
        h.includes("document") || h.includes("sales order") || h.includes("order") ||
        h.includes("invoice") || h.includes("product") || h.includes("customer") ||
        h.includes("category") || h.includes("brand") || h.includes("code") || h.includes("name")
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
        const docIdx = headers.findIndex(h => h.includes("document") || h.includes("sales order") || h.includes("order") || h.includes("invoice"));
        if(docIdx >= 0 && cells[docIdx]) label = cells[docIdx];
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

  function escapeHtml(value){
    return String(value == null ? "" : value).replace(/[&<>"']/g, ch => ({
      "&":"&amp;", "<":"&lt;", ">":"&gt;", '"':"&quot;", "'":"&#39;"
    }[ch]));
  }

  function getChartMetricLabel(item){
    if(item.metric === "revenue") return "Amount";
    if(item.metric === "score") return "Score";
    if(item.metric === "qty") return "Quantity";
    return "Value";
  }

  function ensureChartTooltip(){
    let tip = document.getElementById("rank-chart-tooltip");
    if(!tip){
      tip = document.createElement("div");
      tip.id = "rank-chart-tooltip";
      tip.className = "rank-chart-tooltip";
      document.body.appendChild(tip);
    }
    return tip;
  }

  function bindChartTooltip(el, item, total, max){
    if(!el || !item) return;
    const pctTotal = total ? (item.value / total) * 100 : 0;
    const pctMax = max ? (item.value / max) * 100 : 0;
    const html = `<strong>${escapeHtml(item.label)}</strong><span>${escapeHtml(getChartMetricLabel(item))}: ${escapeHtml(formatChartValue(item))}</span><br><span>Share: ${pctTotal.toFixed(1)}% Â· Versus top: ${pctMax.toFixed(1)}%</span>`;
    const move = ev => {
      const tip = ensureChartTooltip();
      tip.innerHTML = html;
      tip.style.display = "block";
      const pad = 14;
      const rect = tip.getBoundingClientRect();
      let x = ev.clientX + pad;
      let y = ev.clientY + pad;
      if(x + rect.width > window.innerWidth - 8) x = ev.clientX - rect.width - pad;
      if(y + rect.height > window.innerHeight - 8) y = ev.clientY - rect.height - pad;
      tip.style.left = `${Math.max(8, x)}px`;
      tip.style.top = `${Math.max(8, y)}px`;
    };
    el.addEventListener("mousemove", move);
    el.addEventListener("mouseenter", move);
    el.addEventListener("mouseleave", () => {
      const tip = document.getElementById("rank-chart-tooltip");
      if(tip) tip.style.display = "none";
    });
  }

  function addChartHeader(chart, data, type, compact, showValues){
    const total = data.reduce((sum, item) => sum + item.value, 0);
    const title = document.createElement("div");
    title.className = "rank-chart-title";
    title.innerHTML = `<span>${escapeHtml((type || "bar").replace(/\b\w/g, ch => ch.toUpperCase()))} chart</span><span class="rank-chart-subtitle">${data.length} records Â· Total ${escapeHtml(formatChartValue({...data[0], value: total}))}</span>`;
    chart.appendChild(title);

    const toolbar = document.createElement("div");
    toolbar.className = "rank-chart-toolbar";
    const sizeBtn = document.createElement("button");
    sizeBtn.type = "button";
    sizeBtn.className = "chart-toggle";
    sizeBtn.textContent = compact ? "Large view" : "Compact view";
    sizeBtn.addEventListener("click", () => {
      chart.classList.toggle("compact");
      chart.classList.toggle("large");
      sizeBtn.textContent = chart.classList.contains("compact") ? "Large view" : "Compact view";
    });
    const valueBtn = document.createElement("button");
    valueBtn.type = "button";
    valueBtn.className = "chart-toggle active";
    valueBtn.textContent = showValues ? "Hide values" : "Show values";
    valueBtn.addEventListener("click", () => {
      chart.classList.toggle("hide-values");
      const hidden = chart.classList.contains("hide-values");
      valueBtn.classList.toggle("active", !hidden);
      valueBtn.textContent = hidden ? "Show values" : "Hide values";
      chart.querySelectorAll(".rank-chart-value, .svg-chart-value").forEach(v => v.style.display = hidden ? "none" : "");
    });
    toolbar.appendChild(sizeBtn);
    toolbar.appendChild(valueBtn);
    chart.appendChild(toolbar);
  }

  function renderRankChart(container, data, type="bar", options={}){
    const chart = document.createElement("div");
    chart.className = "rank-chart large";
    const compact = options.compact === true;
    const showValues = options.showValues !== false;
    if(compact){ chart.classList.remove("large"); chart.classList.add("compact"); }
    const max = Math.max(...data.map(x => x.value), 1);
    const total = data.reduce((sum, item) => sum + item.value, 0) || 1;
    addChartHeader(chart, data, type, compact, showValues);

    if(type === "column" || type === "line" || type === "pie"){
      renderSvgChart(chart, data, type, max, total, showValues);
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
      bindChartTooltip(row, item, total, max);

      const value = document.createElement("div");
      value.className = "rank-chart-value";
      value.innerHTML = `${escapeHtml(formatChartValue(item))}<span class="rank-chart-pct">${((item.value / total) * 100).toFixed(1)}%</span>`;
      value.style.display = showValues ? "" : "none";

      row.appendChild(label); row.appendChild(track); row.appendChild(value);
      chart.appendChild(row);
    });

    container.appendChild(chart);
  }

  let lastChartContext = null;

  function rememberChartContext(row, answerText, suggestion=null){
    const data = extractRankChartData(answerText);
    const structured = data.length < 2 ? parseStructuredChart(answerText) : null;
    const chartData = data.length >= 2 ? data : structured?.data || [];
    if(chartData.length < 2) return false;
    lastChartContext = {
      row,
      text: answerText,
      data: chartData,
      suggestion: suggestion || {
        question: "Would you like to display this as a chart?",
        options: [
          {type:"bar", label:"Bar chart"},
          {type:"column", label:"Column chart"},
          {type:"line", label:"Line chart"},
          {type:"pie", label:"Pie chart"}
        ]
      }
    };
    return true;
  }

  function rebuildLastChartContextFromVisibleMessages(){
    const rows = Array.from(msgEl.querySelectorAll(".msg-row.bot")).reverse();
    for(const row of rows){
      const text = row.textContent || "";
      if(rememberChartContext(row, text)) return true;
    }
    return false;
  }

  function isChartFollowup(text){
    const q = String(text || "").toLowerCase();
    return /\b(chart|charts|graph|graphs|visuali[sz]e|plot|bar chart|column chart|line chart|pie chart)\b/.test(q)
      || /\b(convert|cover|turn|make|show|display|render)\b[\s\S]{0,28}\b(char|chart|graph)\b/.test(q)
      || /\b(char|chart)\s*(it|this|that|please)?\b/.test(q);
  }

  function inferChartType(text){
    const q = String(text || "").toLowerCase();
    if(/\bpie\b/.test(q)) return "pie";
    if(/\bline\b/.test(q)) return "line";
    if(/\bcolumn\b/.test(q)) return "column";
    return "bar";
  }

  function addBotChartMessage(userText, type="bar"){
    const row=document.createElement("div"); row.className="msg-row bot has-chart";
    const inner=document.createElement("div"); inner.className="msg-inner";
    const avatar=document.createElement("div"); avatar.className="bot-avatar"; avatar.innerHTML='<svg width="18" height="18" viewBox="0 0 32 32" fill="none" xmlns="http://www.w3.org/2000/svg"><rect width="32" height="32" rx="6" fill="#1a73e8"/><text x="16" y="22" text-anchor="middle" fill="white" font-size="18" font-weight="bold" font-family="Arial">AI</text></svg>';
    const bubble=document.createElement("div"); bubble.className="bubble";
    bubble.textContent = "Here is the previous result as a chart.";
    inner.appendChild(avatar); inner.appendChild(bubble); row.appendChild(inner);
    const time=document.createElement("div"); time.className="msg-time"; time.textContent=formatTime(new Date().toISOString()); row.appendChild(time);
    const actions=document.createElement("div"); actions.className="chart-actions";
    const optionRow=document.createElement("div"); optionRow.className="chart-option-row"; optionRow.style.display="flex";
    let chart=null, activeBtn=null;
    const options = lastChartContext?.suggestion?.options || [
      {type:"bar", label:"Bar chart"},
      {type:"column", label:"Column chart"},
      {type:"line", label:"Line chart"},
      {type:"pie", label:"Pie chart"}
    ];
    function draw(nextType, btn=null){
      if(chart) chart.remove();
      if(activeBtn) activeBtn.classList.remove("active");
      activeBtn = btn || activeBtn;
      if(activeBtn) activeBtn.classList.add("active");
      const wrap=document.createElement("div");
      renderRankChart(wrap, lastChartContext.data, nextType || "bar");
      chart=wrap.firstElementChild;
      actions.appendChild(chart);
      smoothScroll();
    }
    options.forEach(opt => {
      const btn=document.createElement("button");
      btn.type="button";
      btn.className="chart-toggle";
      btn.textContent=opt.label || opt.type || "Chart";
      btn.addEventListener("click",()=>draw(opt.type || "bar", btn));
      optionRow.appendChild(btn);
      if((opt.type || "bar") === type) activeBtn = btn;
    });
    actions.appendChild(optionRow);
    row.appendChild(actions);
    msgEl.appendChild(row);
    draw(type, activeBtn);
    syncLocalExchange(userText, "Here is the previous result as a chart.");
  }

  // URL params â€” optional overrides (avatar, modules passed from widget iframe)
  function renderSvgChart(chart, data, type, max, total, showValues=true){
    const w = 760, h = 300, pad = 42;
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
        const x1 = 180 + 104 * Math.cos(angle), y1 = 148 + 104 * Math.sin(angle);
        const x2 = 180 + 104 * Math.cos(next),  y2 = 148 + 104 * Math.sin(next);
        angle = next;
        return `<path class="rank-chart-point" data-chart-index="${i}" d="M180 148 L${x1.toFixed(2)} ${y1.toFixed(2)} A104 104 0 ${large} 1 ${x2.toFixed(2)} ${y2.toFixed(2)} Z" fill="${colors[i % colors.length]}"><title>${escapeSvg(item.label)}: ${escapeSvg(formatChartValue(item))}</title></path>`;
      }).join("");
      const legend = data.slice(0, 8).map((item, i) =>
        `<g transform="translate(345 ${42 + i * 26})"><rect width="11" height="11" fill="${colors[i % colors.length]}" rx="2"/><text x="17" y="10" font-size="12" fill="#1e3a6e">${escapeSvg(short(item.label))}</text><text class="svg-chart-value" x="260" y="10" text-anchor="end" font-size="12" fill="#6a7d99">${escapeSvg(formatChartValue(item))}</text></g>`
      ).join("");
      const svgWrap = document.createElement("div");
      svgWrap.innerHTML = `<svg viewBox="0 0 760 300" role="img">${slices}${legend}</svg>`;
      chart.appendChild(svgWrap.firstElementChild);
      chart.querySelectorAll(".rank-chart-point").forEach((el, i) => bindChartTooltip(el, data[i], total, max));
      if(!showValues) chart.querySelectorAll(".svg-chart-value").forEach(v => v.style.display = "none");
      return;
    }

    const usableW = w - pad * 2;
    const usableH = h - pad * 2 - 28;
    const axis = `<line x1="${pad}" y1="${pad + usableH}" x2="${w - pad}" y2="${pad + usableH}" stroke="#d8e4f3"/><line x1="${pad}" y1="${pad}" x2="${pad}" y2="${pad + usableH}" stroke="#d8e4f3"/><text x="${pad}" y="${pad - 12}" font-size="11" fill="#6a7d99">${escapeSvg(formatChartValue({...data[0], value: max}))}</text>`;
    const points = data.map((item, i) => {
      const x = pad + (data.length === 1 ? usableW / 2 : (i / (data.length - 1)) * usableW);
      const y = pad + usableH - (item.value / max) * usableH;
      return {x, y, item};
    });

    if(type === "line"){
      const path = points.map((p, i) => `${i ? "L" : "M"}${p.x.toFixed(2)} ${p.y.toFixed(2)}`).join(" ");
      const dots = points.map((p, i) => `<circle class="rank-chart-point" data-chart-index="${i}" cx="${p.x}" cy="${p.y}" r="5" fill="#1e3a6e"><title>${escapeSvg(p.item.label)}: ${escapeSvg(formatChartValue(p.item))}</title></circle>${showValues ? `<text class="svg-chart-value" x="${p.x}" y="${p.y - 10}" text-anchor="middle" font-size="10" fill="#1e3a6e">${escapeSvg(formatChartValue(p.item))}</text>` : ""}`).join("");
      const step = Math.max(1, Math.ceil(points.length / 5));
      const labels = points.map((p, i) => i % step === 0 ? `<text x="${p.x}" y="${h - 8}" text-anchor="middle" font-size="10" fill="#8a9bb5">${escapeSvg(short(p.item.label))}</text>` : "").join("");
      const svgWrap = document.createElement("div");
      svgWrap.innerHTML = `<svg viewBox="0 0 ${w} ${h}" role="img">${axis}<path d="${path}" fill="none" stroke="#1e3a6e" stroke-width="3"/>${dots}${labels}</svg>`;
      chart.appendChild(svgWrap.firstElementChild);
      chart.querySelectorAll(".rank-chart-point").forEach((el, i) => bindChartTooltip(el, data[i], total, max));
      return;
    }

    const gap = 12;
    const barW = Math.max(10, (usableW - gap * (data.length - 1)) / data.length);
    const bars = data.map((item, i) => {
      const bh = Math.max(2, (item.value / max) * usableH);
      const x = pad + i * (barW + gap);
      const y = pad + usableH - bh;
      return `<rect class="rank-chart-point" data-chart-index="${i}" x="${x}" y="${y}" width="${barW}" height="${bh}" rx="4" fill="#1e3a6e"><title>${escapeSvg(item.label)}: ${escapeSvg(formatChartValue(item))}</title></rect>${showValues ? `<text class="svg-chart-value" x="${x + barW / 2}" y="${Math.max(14, y - 8)}" text-anchor="middle" font-size="10" fill="#1e3a6e">${escapeSvg(formatChartValue(item))}</text>` : ""}<text x="${x + barW / 2}" y="${h - 8}" text-anchor="middle" font-size="10" fill="#8a9bb5">${escapeSvg(short(item.label))}</text>`;
    }).join("");
    const svgWrap = document.createElement("div");
    svgWrap.innerHTML = `<svg viewBox="0 0 ${w} ${h}" role="img">${axis}${bars}</svg>`;
    chart.appendChild(svgWrap.firstElementChild);
    chart.querySelectorAll(".rank-chart-point").forEach((el, i) => bindChartTooltip(el, data[i], total, max));
  }

  function renderChartSuggestion(row, suggestion, text){
    const data = extractRankChartData(text);
    if(!suggestion) return;
    rememberChartContext(row, text, suggestion);
    row.classList.add("has-chart");

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

  //â”€â”€ DOM refs â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
  const msgEl   = document.getElementById("messages");
  const recentEl = document.getElementById("recent-list");
  const recentSearchEl = document.getElementById("recent-search");
  if(recentSearchEl){
    recentSearchEl.addEventListener("input", () => renderRecentChats(recentSearchEl.value));
  }
  const inputEl = document.getElementById("user-input");
  const sendBtn = document.getElementById("send-btn");
  let unreadCount = 0, isVisible = true;

  //â”€â”€ Widget bridge â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
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

  //â”€â”€ Scroll â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
  let scrollRaf = null;
  function smoothScroll(){
    if(scrollRaf) cancelAnimationFrame(scrollRaf);
    scrollRaf = requestAnimationFrame(()=>{ msgEl.scrollTop = msgEl.scrollHeight; });
  }

  //â”€â”€ Helpers â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
  function formatTime(iso){ return iso?new Date(iso).toLocaleTimeString([],{hour:"2-digit",minute:"2-digit"}):""; }
  function formatDate(iso){ return iso?new Date(iso).toLocaleDateString([],{day:"2-digit",month:"short",year:"numeric"}):""; }
  function escHtml(t){ return(t||"").replace(/&/g,"&amp;").replace(/</g,"&lt;").replace(/>/g,"&gt;"); }

  //â”€â”€ Lightbox â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
  function openLightbox(src){ document.getElementById("lightbox-img").src=src; document.getElementById("lightbox").classList.add("open"); }
  function closeLightbox(){ document.getElementById("lightbox").classList.remove("open"); }
  document.getElementById("lightbox").addEventListener("click",function(e){ if(e.target===this)closeLightbox(); });

  //â”€â”€ Avatars â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
  function userAvatarHtml(){
    const url=getAvatarUrl(), init=USER_ID[0].toUpperCase();
    if(url) return `<div class="user-avatar"><img src="${url}" onerror="this.parentElement.textContent='${init}'"/></div>`;
    return `<div class="user-avatar">${init}</div>`;
  }

  //â”€â”€ Typewriter â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
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

  //â”€â”€ Static message helpers â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
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
    if(SHOW_SOURCES && sources?.length){ const s=document.createElement("div"); s.className="msg-sources"; s.innerHTML=`ðŸ“„ <span>${sources.map(s=>s.split(/[\\/]/).pop()).join(", ")}</span>`; row.appendChild(s); }
    msgEl.appendChild(row);
    rememberChartContext(row, text);
    if(!isVisible&&scroll){ unreadCount++; notifyUnread(unreadCount); }
    if(scroll) smoothScroll();
  }

  //â”€â”€ Streaming bot row â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
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
        renderMessageContent(d, text);
        smoothScroll();
        if(onDone) onDone();
      },

      addStep(text, img, isMulti, stepIndex, onDone){
        this.hideDots();
        const block=document.createElement("div"); block.className="step-block";
        const textEl=document.createElement("div"); textEl.className="step-text";
        block.appendChild(textEl); bubble.appendChild(block);
        stepBlocks[stepIndex] = block;
        renderMessageContent(textEl, `${stepIndex+1}. `+text);
        const shown = appendImage(block, img);
        if(shown){
          const imgEl = block.querySelector(".step-image img");
          if(imgEl){
            imgEl.onload=()=>{ smoothScroll(); if(onDone) setTimeout(onDone,50); };
            setTimeout(()=>{ if(onDone) onDone(); }, 2000);
            return;
          }
        }
        smoothScroll();
        if(onDone) onDone();
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
        renderMessageContent(inner, text);
        smoothScroll();
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
        if(SHOW_SOURCES && sources?.length){ const s=document.createElement("div"); s.className="msg-sources"; s.innerHTML=`ðŸ“„ <span>${sources.map(s=>s.split(/[\\/]/).pop()).join(", ")}</span>`; row.appendChild(s); }
        if(chartSuggestion) renderChartSuggestion(row, chartSuggestion, answer);
        else rememberChartContext(row, answer);
        if(question&&answer){
          const ts=Date.now();
          const fbRow=document.createElement("div"); fbRow.className="feedback-row";
          fbRow.innerHTML=`<span>Helpful?</span><button class="fb-btn" id="fy-${ts}">ðŸ‘ Yes</button><button class="fb-btn" id="fn-${ts}">ðŸ‘Ž No</button>`;
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
            yBtn.classList.remove("loading"); yBtn.className="fb-btn confirmed"; yBtn.textContent="âœ“ Thanks!";
          });

          nBtn.addEventListener("click",()=>{
            yBtn.classList.add("dismissed");
            nBtn.className="fb-btn confirmed"; nBtn.textContent="ðŸ‘Ž";
            panel.style.display="block"; smoothScroll();
          });

          panel.querySelector(`#fbc-${ts}`).addEventListener("click",()=>{
            panel.style.display="none";
            nBtn.className="fb-btn"; nBtn.textContent="ðŸ‘Ž No";
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
              if(pref.response_len==="detailed")      msg="Got it! I'll give more detailed answers from now on ðŸ˜Š";
              else if(pref.response_len==="short")     msg="Got it! I'll keep my answers more concise from now on ðŸ˜Š";
              else if(pref.language==="vi")             msg="ÄÆ°á»£c rá»“i! TÃ´i sáº½ tráº£ lá»i báº±ng tiáº¿ng Viá»‡t tá»« bÃ¢y giá» ðŸ˜Š";
              else if(pref.language==="en")             msg="Got it! I'll reply in English from now on ðŸ˜Š";
              if(msg){
                const toast=document.createElement("div");
                toast.style.cssText="font-size:12px;color:var(--clr-primary);margin-top:6px;padding:4px 0;";
                toast.textContent="âœ¨ "+msg; panel.appendChild(toast);
              }
            }
            panel.querySelector(".fb-reasons").style.display="none";
            panel.querySelector(".fb-comment").style.display="none";
            panel.querySelector(".fb-actions").style.display="none";
            panel.querySelector(".fb-panel-title").textContent="âœ“ Thank you for your feedback!";
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

  //â”€â”€ Typing indicator â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
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

  //â”€â”€ History â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
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

  //â”€â”€ Input handlers â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
  inputEl.addEventListener("input",()=>{ inputEl.style.height="auto"; inputEl.style.height=inputEl.scrollHeight+"px"; });
  inputEl.addEventListener("keydown",e=>{ if(e.key==="Enter"&&!e.shiftKey){ e.preventDefault(); sendMessage(); } });
  sendBtn.addEventListener("click",sendMessage);
  document.addEventListener("visibilitychange",()=>{ isVisible=!document.hidden; if(isVisible){ unreadCount=0; notifyUnread(0); } });

  function syncLocalExchange(userText, assistantText){
    const ts = new Date().toISOString();
    currentSessionMessages = currentSessionMessages.concat([
      {role:"user", content:userText, timestamp:ts},
      {role:"assistant", content:assistantText, timestamp:ts}
    ]);
    updateSessionStrip(currentSessionMessages.length);
    const sessionItem = recentChats.find(item => item.id === currentSessionId);
    if(sessionItem){
      sessionItem.messages = currentSessionMessages.slice();
      sessionItem.msgCount = currentSessionMessages.length;
      sessionItem.updatedAt = ts;
      sessionItem.hasMore = currentSessionHasMore;
      sessionItem.oldestId = currentSessionOldestId;
      sessionItem._cachedHtml = "";
    }
  }

  //â”€â”€ Send message â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
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

    if(isChartFollowup(text) && (!lastChartContext || lastChartContext.data?.length < 2)){
      rebuildLastChartContextFromVisibleMessages();
    }
    if(isChartFollowup(text) && lastChartContext && lastChartContext.data?.length >= 2){
      addBotChartMessage(text, inferChartType(text));
      sendBtn.disabled=false; inputEl.focus();
      return;
    }

    const typing=addTypingIndicator();
    let streamRow=null, allSteps=[], sources=[], versionIds=[], receivedDone=false, introText="", chartSuggestion=null;

    // Step queue â€” process one step at a time for sequential typewriter effect
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
                  addBotMessage("âš ï¸ I could not generate an answer for that request. Please try rephrasing it or check that the ERP data service is running.",[],new Date().toISOString());
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
          addBotMessage("âš ï¸ I could not generate an answer for that request. Please try rephrasing it or check that the ERP data service is running.",[],new Date().toISOString());
        }
      }
    }catch(err){
      console.error("Chat stream error:", err);
      typing.remove();
      if(!streamRow){
        addBotMessage("âš ï¸ Cannot connect to AI server. Make sure the API is running.",[],null);
      }
    }
    sendBtn.disabled=false; inputEl.focus();
  }

  //â”€â”€ Feedback â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
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

