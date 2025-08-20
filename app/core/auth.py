# app/core/auth.py
import secrets
from datetime import datetime, timedelta
from typing import Dict, Optional
from fastapi import HTTPException, Request, Depends, status

# Simple in-memory session store
sessions: Dict[str, Dict] = {}


def create_session(user_id: int, username: str) -> str:
    """Create session and return session ID"""
    session_id = secrets.token_urlsafe(32)
    sessions[session_id] = {
        'user_id': user_id,
        'username': username,
        'expires_at': datetime.utcnow() + timedelta(hours=1)
    }
    return session_id


def get_session(session_id: str) -> Optional[Dict]:
    """Get session if valid"""
    if session_id not in sessions:
        return None

    session = sessions[session_id]
    if datetime.utcnow() > session['expires_at']:
        del sessions[session_id]
        return None

    return session


def delete_session(session_id: str):
    """Delete session"""
    sessions.pop(session_id, None)


def require_auth(request: Request):
    """Auth dependency - use this to protect routes"""
    session_id = request.cookies.get("session_id")

    if not session_id:
        raise HTTPException(status_code=401, detail="Not authenticated")

    session = get_session(session_id)
    if not session:
        raise HTTPException(status_code=401, detail="Session expired")

    return session
