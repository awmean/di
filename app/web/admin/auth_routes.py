# First, install jinja2 and python-multipart:
# pip install jinja2 python-multipart

# app/web/admin/auth_routes.py
from fastapi import APIRouter, Depends, Response, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from app.core.auth import create_session, delete_session, require_auth, get_session
from app.core.database import get_db
from app.repositories.admin_user_repository import AdminUserRepository

router = APIRouter()
templates = Jinja2Templates(directory="templates/admin")


@router.get("/login", response_class=HTMLResponse)
def login_page(request: Request):
    session_id = request.cookies.get("session_id")
    if session_id and get_session(session_id):
        return RedirectResponse(url="/admin/home", status_code=302)

    return templates.TemplateResponse("login.html", {"request": request})


@router.post("/login")
def login(
        request: Request,
        response: Response,
        username: str = Form(...),
        password: str = Form(...),
        db: Session = Depends(get_db)
):
    user = AdminUserRepository.authenticate(db, username, password)

    if not user:
        return templates.TemplateResponse(
            "login.html",
            {"request": request, "error": "Invalid username or password"}
        )

    session_id = create_session(user.id, user.username)

    response = RedirectResponse(url="/admin/home", status_code=302)
    response.set_cookie(
        key="session_id",
        value=session_id,
        httponly=True,
        max_age=3600
    )

    return response


@router.get("/home", response_class=HTMLResponse)
def admin_home(request: Request, session=Depends(require_auth), db: Session = Depends(get_db)):
    user = AdminUserRepository.get_by_id(db, session['user_id'])
    return templates.TemplateResponse(
        "home.html",
        {"request": request, "user": user}
    )


@router.post("/logout")
def logout(request: Request):
    session_id = request.cookies.get("session_id")
    if session_id:
        delete_session(session_id)

    response = RedirectResponse(url="/admin/login", status_code=302)
    response.delete_cookie("session_id")
    return response
