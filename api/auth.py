"""
ERP AI Assistant — Authentication
API Key verification via X-API-Key header.
"""
from fastapi import Depends, HTTPException
from fastapi.security import APIKeyHeader

from api.config import CHAT_API_KEY

api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)


def verify_api_key(key: str = Depends(api_key_header)):
    """Verify the X-API-Key header matches configured CHAT_API_KEY."""
    if key != CHAT_API_KEY:
        raise HTTPException(status_code=403, detail="Invalid or missing API key")
    return key
