from fastapi import Depends, Response, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy.orm import Session

from app.admin_users.repository import AdminUserRepository
from app.core.auth import create_session, delete_session, get_session
from app.core.database import get_db
from app.web.admin import router, templates


@router.get('/', response_class=RedirectResponse)
def root(request: Request):
    session_id = request.cookies.get("session_id")
    if session_id and get_session(session_id):
        return RedirectResponse(url="/admin/dashboard", status_code=302)
    else:
        return RedirectResponse(url="/admin/login", status_code=302)


# Updated login routes
@router.get("/login", response_class=HTMLResponse)
def login_page(request: Request, next: str = None):
    session_id = request.cookies.get("session_id")
    if session_id and get_session(session_id):
        # If already logged in, redirect to 'next' URL or default dashboard
        redirect_url = next if next else "/admin/dashboard"
        return RedirectResponse(url=redirect_url, status_code=302)

    return templates.TemplateResponse("login.html", {
        "request": request,
        "next": next  # Pass the next parameter to template
    })


@router.post("/login")
def login(
        request: Request,
        response: Response,
        username: str = Form(...),
        password: str = Form(...),
        next: str = Form(None),  # Capture next parameter from form
        db: Session = Depends(get_db)
):
    user = AdminUserRepository.authenticate(db, username, password)

    if not user:
        return templates.TemplateResponse(
            "login.html",
            {
                "request": request,
                "error": "Invalid username or password",
                "next": next  # Preserve next parameter on error
            }
        )

    session_id = create_session(user.id, user.username)

    # Redirect to the original URL or default dashboard
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
def logout(request: Request):
    session_id = request.cookies.get("session_id")
    if session_id:
        delete_session(session_id)

    response = RedirectResponse(url="/admin/login", status_code=302)
    response.delete_cookie("session_id")
    return response
