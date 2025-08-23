# app/core/auth.py
import secrets
from datetime import datetime, timedelta
from typing import Dict, Optional
from urllib.parse import quote

from fastapi import HTTPException, Request, status

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
        # Capture the current URL and redirect to login with 'next' parameter
        current_url = str(request.url)
        login_url = f"/admin/login?next={quote(current_url)}"
        raise HTTPException(
            status_code=status.HTTP_302_FOUND,
            headers={"Location": login_url}
        )

    session = get_session(session_id)
    if not session:
        # Capture the current URL and redirect to login with 'next' parameter
        current_url = str(request.url)
        login_url = f"/admin/login?next={quote(current_url)}"
        raise HTTPException(
            status_code=status.HTTP_302_FOUND,
            headers={"Location": login_url}
        )

    return session
