import json
import secrets
from datetime import datetime, timedelta
from typing import Dict, Optional
from urllib.parse import quote

from fastapi import HTTPException, Request, status

from app.core.redis import get_redis


async def create_session(user_id: int, username: str) -> str:
    """Create session and return session ID"""
    session_id = secrets.token_urlsafe(32)
    session_data = {
        "user_id": user_id,
        "username": username,
        "expires_at": (datetime.utcnow() + timedelta(hours=1)).isoformat(),
    }

    redis_client = await get_redis()
    await redis_client.setex(
        f"session:{session_id}",
        3600,  # 1 час в секундах
        json.dumps(session_data)
    )

    return session_id


async def get_session(session_id: str) -> Optional[Dict]:
    """Get session if valid"""
    redis_client = await get_redis()
    session_data = await redis_client.get(f"session:{session_id}")

    if not session_data:
        return None

    session = json.loads(session_data)
    expires_at = datetime.fromisoformat(session["expires_at"])

    if datetime.utcnow() > expires_at:
        await redis_client.delete(f"session:{session_id}")
        return None

    return session


async def delete_session(session_id: str):
    """Delete session"""
    redis_client = await get_redis()
    await redis_client.delete(f"session:{session_id}")


async def require_auth(request: Request):
    """Auth dependency - use this to protect routes"""
    session_id = request.cookies.get("session_id")

    if not session_id:
        # Capture the current URL and redirect to login with 'next' parameter
        current_url = str(request.url)
        login_url = f"/admin/login?next={quote(current_url)}"
        raise HTTPException(
            status_code=status.HTTP_302_FOUND, headers={"Location": login_url}
        )

    session = await get_session(session_id)
    if not session:
        # Capture the current URL and redirect to login with 'next' parameter
        current_url = str(request.url)
        login_url = f"/admin/login?next={quote(current_url)}"
        raise HTTPException(
            status_code=status.HTTP_302_FOUND, headers={"Location": login_url}
        )

    return session


# Дополнительные функции для управления сессиями

async def extend_session(session_id: str, hours: int = 1):
    """Продлить срок действия сессии"""
    session = await get_session(session_id)
    if session:
        session["expires_at"] = (datetime.utcnow() + timedelta(hours=hours)).isoformat()
        redis_client = await get_redis()
        await redis_client.setex(
            f"session:{session_id}",
            hours * 3600,
            json.dumps(session)
        )


async def get_all_user_sessions(user_id: int) -> list:
    """Получить все активные сессии пользователя"""
    redis_client = await get_redis()
    session_keys = await redis_client.keys("session:*")

    user_sessions = []
    for key in session_keys:
        session_data = await redis_client.get(key)
        if session_data:
            session = json.loads(session_data)
            if session.get("user_id") == user_id:
                user_sessions.append({
                    "session_id": key.replace("session:", ""),
                    **session
                })

    return user_sessions


async def delete_all_user_sessions(user_id: int):
    """Удалить все сессии пользователя (например, при смене пароля)"""
    user_sessions = await get_all_user_sessions(user_id)
    redis_client = await get_redis()

    for session in user_sessions:
        await redis_client.delete(f"session:{session['session_id']}")
