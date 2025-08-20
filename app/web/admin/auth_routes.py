from fastapi import APIRouter, Depends, HTTPException, Response, Request
from sqlalchemy.orm import Session

from app.core.auth import create_session, delete_session, require_auth
from app.core.database import get_db
from app.repositories.admin_user_repository import AdminUserRepository
from app.schemas.admin_user import AdminUserLogin

router = APIRouter()


@router.post("/login")
def login(response: Response, login_data: AdminUserLogin, db: Session = Depends(get_db)):
    user = AdminUserRepository.authenticate(db, login_data.username, login_data.password)

    if not user:
        raise HTTPException(status_code=401, detail="Invalid credentials")

    session_id = create_session(user.id, user.username)

    response.set_cookie(
        key="session_id",
        value=session_id,
        httponly=True,
        max_age=3600  # 1 hour
    )

    return {"message": "Login successful"}


@router.post("/logout")
def logout(response: Response, request: Request):
    session_id = request.cookies.get("session_id")
    if session_id:
        delete_session(session_id)

    response.delete_cookie("session_id")
    return {"message": "Logged out"}


@router.get("/me")
def get_me(session=Depends(require_auth), db: Session = Depends(get_db)):
    user = AdminUserRepository.get_by_id(db, session['user_id'])
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    return {
        "id": user.id,
        "username": user.username,
        "email": user.email
    }
