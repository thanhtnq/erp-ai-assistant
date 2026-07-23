"""
ERP AI Assistant — Chat Router
Endpoints: /chat/stream, /chat/history, /chat/history/delete, /chat/greeting, /chat/preferences
"""
import asyncio
import json
import uuid
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from starlette.requests import Request

from api.auth import verify_api_key
from api.models import ChatRequest, ChatHistoryRequest, ChatHistoryDeleteRequest
from api.database import get_chat_conn
from api.chat import (
    get_user_prefs, update_user_prefs, detect_pref_change,
    get_history, get_session_history, format_history, save_message,
    generate_chat_stream, build_system_prompt,
    get_sessions, create_session, update_session_title, delete_session,
    delete_recent_conversation,
)
from api.llm import _gemini_client, LLM_MODEL, GREETING_PROMPT

router = APIRouter()


def _normalize_chat_body(body: ChatRequest) -> ChatRequest:
    """Accept both legacy CFML `text` and newer API `query` payloads."""
    if not body.query and body.text:
        body.query = body.text
    if not body.text and body.query:
        body.text = body.query
    if not body.query:
        raise HTTPException(status_code=400, detail="query is required")
    return body


@router.post("/stream")
async def chat_stream(
    body: ChatRequest,
    request: Request,
    _key: str = Depends(verify_api_key),
):
    """SSE streaming chat endpoint."""
    body = _normalize_chat_body(body)
    prefs = get_user_prefs(body.user_id, body.company_id)

    # Detect preference changes in the query
    pref_changes = detect_pref_change(body.query)
    if pref_changes:
        update_user_prefs(body.user_id, body.company_id, **pref_changes)
        prefs.update(pref_changes)

    if not body.session_id:
        body.session_id = str(uuid.uuid4())
    create_session(
        body.user_id,
        body.company_id,
        body.session_id,
        body.query[:80].strip() or "Untitled chat",
    )

    system_prompt = build_system_prompt(prefs)
    history_rows, _ = get_session_history(
        body.user_id,
        body.company_id,
        body.session_id,
        limit=50,
    )
    history_text = format_history(history_rows)

    return StreamingResponse(
        generate_chat_stream(body, history_text, prefs, system_prompt),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


@router.post("/history")
async def chat_history(
    body: ChatHistoryRequest,
    _key: str = Depends(verify_api_key),
):
    """Get chat history for a user."""
    conn = get_chat_conn()
    params = [body.user_id, body.company_id]
    query = """
        SELECT id, role, content, timestamp
        FROM chat_history
        WHERE user_id=? AND company_id=?
    """
    if body.session_id:
        query += " AND session_id=?"
        params.append(body.session_id)
    if body.before_id:
        query += " AND id < ?"
        params.append(body.before_id)
    query += " ORDER BY id DESC LIMIT ?"
    params.append(body.limit + 1)
    rows = conn.execute(query, params).fetchall()
    conn.close()
    has_more = len(rows) > body.limit
    rows = rows[:body.limit]
    return {
        "history": [
            {"id": r["id"], "role": r["role"], "content": r["content"],
             "timestamp": r["timestamp"]}
            for r in rows
        ],
        "has_more": has_more,
        "oldest_id": rows[-1]["id"] if rows else None,
    }


@router.post("/history/delete")
async def chat_history_delete(
    body: ChatHistoryDeleteRequest,
    _key: str = Depends(verify_api_key),
):
    """Delete chat history for a user."""
    conn = get_chat_conn()
    conn.execute(
        "DELETE FROM chat_history WHERE user_id=? AND company_id=?",
        (body.user_id, body.company_id)
    )
    conn.execute(
        "DELETE FROM chat_result_context WHERE user_id=? AND company_id=?",
        (body.user_id, body.company_id)
    )
    conn.commit()
    conn.close()
    return {"status": "deleted"}


@router.post("/greeting")
async def chat_greeting(
    body: ChatRequest,
    _key: str = Depends(verify_api_key),
):
    """Generate a greeting message for the user."""
    if not body.query and not body.text:
        body.query = "hello"
        body.text = "hello"
    prefs = get_user_prefs(body.user_id, body.company_id)
    system_prompt = build_system_prompt(prefs)
    history_rows, _ = get_session_history(
        body.user_id,
        body.company_id,
        body.session_id,
        limit=50,
    )
    history_text = format_history(history_rows)

    prompt = GREETING_PROMPT.format(
        system_prompt=system_prompt,
        history=history_text,
    )
    try:
        resp = await asyncio.wait_for(
            asyncio.to_thread(
                _gemini_client.models.generate_content,
                model=LLM_MODEL,
                contents=[{"role": "user", "parts": [{"text": prompt}]}],
            ),
            timeout=4,
        )
        greeting = resp.text.strip() if resp.text else "Hello! How can I help you today?"
    except Exception:
        greeting = "How can I help you today?"
    return {"greeting": greeting, "message": greeting}


@router.get("/preferences")
async def chat_preferences_get(
    user_id: str = "user_001",
    company_id: str = "",
    _key: str = Depends(verify_api_key),
):
    """Get user preferences."""
    return get_user_prefs(user_id, company_id)


@router.post("/preferences")
async def chat_preferences_update(
    body: dict,
    _key: str = Depends(verify_api_key),
):
    """Update user preferences."""
    update_user_prefs(
        body.get("user_id", "user_001"),
        body.get("company_id", ""),
        language=body.get("language"),
        response_len=body.get("response_len"),
    )
    return {"status": "updated"}


# ─── Session Management ────────────────────────────────────────────────────────


@router.post("/sessions")
async def chat_sessions_list(
    body: dict,
    _key: str = Depends(verify_api_key),
):
    """Get all sessions for a user."""
    sessions = get_sessions(
        body.get("user_id", "user_001"),
        body.get("company_id", ""),
    )
    return {"sessions": sessions}


@router.post("/sessions/create")
async def chat_session_create(
    body: dict,
    _key: str = Depends(verify_api_key),
):
    """Create a new chat session."""
    import uuid
    session_id = body.get("session_id") or str(uuid.uuid4())
    title = body.get("title", "Untitled chat")
    create_session(
        body.get("user_id", "user_001"),
        body.get("company_id", ""),
        session_id,
        title,
    )
    return {"session_id": session_id, "title": title}


@router.post("/sessions/rename")
async def chat_session_rename(
    body: dict,
    _key: str = Depends(verify_api_key),
):
    """Rename a chat session."""
    session_id = body.get("session_id", "")
    title = body.get("title", "Untitled chat")
    if not session_id:
        raise HTTPException(status_code=400, detail="session_id is required")
    update_session_title(session_id, title)
    return {"status": "renamed", "session_id": session_id, "title": title}


@router.post("/sessions/delete")
async def chat_session_delete(
    body: dict,
    _key: str = Depends(verify_api_key),
):
    """Delete a chat session and all its messages."""
    session_id = body.get("session_id", "")
    if not session_id:
        raise HTTPException(status_code=400, detail="session_id is required")
    delete_session(
        session_id,
        body.get("user_id", "user_001"),
        body.get("company_id", ""),
    )
    return {"status": "deleted", "session_id": session_id}


@router.post("/recent/delete")
async def chat_recent_delete(
    body: dict,
    _key: str = Depends(verify_api_key),
):
    """Delete one recent conversation built from chat_history rows."""
    start_message_id = body.get("start_message_id")
    if not start_message_id:
        raise HTTPException(status_code=400, detail="start_message_id is required")
    try:
        start_message_id = int(start_message_id)
    except (TypeError, ValueError):
        raise HTTPException(status_code=400, detail="start_message_id must be an integer")

    deleted = delete_recent_conversation(
        body.get("user_id", "user_001"),
        body.get("company_id", ""),
        start_message_id,
    )
    if not deleted:
        raise HTTPException(status_code=404, detail="recent conversation not found")
    return {"status": "deleted", "deleted": deleted, "start_message_id": start_message_id}
