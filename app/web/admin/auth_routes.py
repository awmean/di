from fastapi import Depends, Response, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy.orm import Session

from app.admin_users.repository import AdminUserRepository
from app.core.auth import create_session, delete_session, require_auth
from app.core.database import get_db
from app.web.admin import router, templates


@router.get('/')
def root():
    """Root admin page - require_auth автоматически редиректит на логин если нужно"""
    return RedirectResponse(url="/admin/dashboard", status_code=302)


@router.get("/login", response_class=HTMLResponse)
def login_page(request: Request, next: str = None):
    """Страница логина - доступна всем"""
    return templates.TemplateResponse("login.html", {
        "request": request,
        "next": next
    })


@router.post("/login")
def login(
        request: Request,
        response: Response,
        username: str = Form(...),
        password: str = Form(...),
        next: str = Form(None),
        db: Session = Depends(get_db)
):
    """Обработка логина - доступна всем"""
    user = AdminUserRepository.authenticate(db, username, password)

    if not user:
        return templates.TemplateResponse(
            "login.html",
            {
                "request": request,
                "error": "Invalid username or password",
                "next": next
            }
        )

    session_id = create_session(user.id, user.username)

    # Редирект на оригинальный URL или dashboard по умолчанию
    redirect_url = next if next else "/admin/dashboard"
    response = RedirectResponse(url=redirect_url, status_code=302)
    response.set_cookie(
        key="session_id",
        value=session_id,
        httponly=True,
        max_age=3600
    )

    return response


@router.post("/logout")
def logout(request: Request, session=Depends(require_auth)):
    """Логаут - только для авторизованных пользователей"""
    session_id = request.cookies.get("session_id")
    if session_id:
        delete_session(session_id)

    response = RedirectResponse(url="/admin/login", status_code=302)
    response.delete_cookie("session_id")
    return response