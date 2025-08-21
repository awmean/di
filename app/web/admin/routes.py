from fastapi import Request, Depends
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from app.core.auth import require_auth
from app.core.database import get_db
from app.repositories.admin_user_repository import AdminUserRepository
from app.repositories.category_repository import CategoryRepository
from app.repositories.order_repository import OrderRepository
from app.repositories.product_repository import ProductRepository
from app.web.admin import router, templates

admin_templates = Jinja2Templates(directory="templates/admin")


@router.get("/dashboard", response_class=HTMLResponse)
def admin_home(request: Request, session=Depends(require_auth), db: Session = Depends(get_db)):
    user = AdminUserRepository.get_by_id(db, session['user_id'])
    return templates.TemplateResponse(
        "dashboard.html",
        {"request": request, "user": user}
    )


@router.get('/products', response_class=HTMLResponse)
def admin_products(request: Request, session=Depends(require_auth), db: Session = Depends(get_db)):
    user = AdminUserRepository.get_by_id(db, session['user_id'])
    products = ProductRepository.get_all(db)
    return templates.TemplateResponse(
        "products.html",
        {"request": request, "user": user, "products": products}
    )


@router.get('/products/create', response_class=HTMLResponse)
def admin_products(request: Request, session=Depends(require_auth), db: Session = Depends(get_db)):
    user = AdminUserRepository.get_by_id(db, session['user_id'])
    products = ProductRepository.get_all(db)
    categories = CategoryRepository.get_all(db)
    return templates.TemplateResponse(
        "product_create.html",
        {"request": request, "user": user, "products": products, 'categories': categories}
    )


@router.get('/products/{product_id}/edit', response_class=HTMLResponse)
def admin_products(product_id: int, request: Request, session=Depends(require_auth), db: Session = Depends(get_db)):
    user = AdminUserRepository.get_by_id(db, session['user_id'])
    product = ProductRepository.get_by_id(db, product_id=product_id)
    categories = CategoryRepository.get_all(db)
    return templates.TemplateResponse(
        "product_edit.html",
        {"request": request, "user": user, "product": product, 'categories': categories}
    )


@router.get('/categories', response_class=HTMLResponse)
def admin_categories(request: Request, session=Depends(require_auth), db: Session = Depends(get_db)):
    user = AdminUserRepository.get_by_id(db, session['user_id'])
    categories = CategoryRepository.get_all(db)
    return templates.TemplateResponse(
        "categories.html",
        {"request": request, "user": user, "categories": categories}
    )


@router.get('/categories/create', response_class=HTMLResponse)
def admin_categories(request: Request, session=Depends(require_auth), db: Session = Depends(get_db)):
    user = AdminUserRepository.get_by_id(db, session['user_id'])
    categories = CategoryRepository.get_all(db)
    return templates.TemplateResponse(
        "category_create.html",
        {"request": request, "user": user, "categories": categories}
    )


@router.get('/categories/{category_id}/edit', response_class=HTMLResponse)
def admin_categories(category_id: int, request: Request, session=Depends(require_auth), db: Session = Depends(get_db)):
    user = AdminUserRepository.get_by_id(db, session['user_id'])
    category = CategoryRepository.get_by_id(db, category_id)
    return templates.TemplateResponse(
        "category_edit.html",
        {"request": request, "user": user, 'category_id': category_id, 'category': category}
    )


@router.get('/orders', response_class=HTMLResponse)
def admin_categories(request: Request, session=Depends(require_auth), db: Session = Depends(get_db)):
    user = AdminUserRepository.get_by_id(db, session['user_id'])
    orders = OrderRepository.get_all(db)
    return templates.TemplateResponse(
        "orders.html",
        {"request": request, "user": user, "orders": orders}
    )
