from fastapi import APIRouter, Request, Depends
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.repositories.admin_user_repository import AdminUserRepository
from app.repositories.category_repository import CategoryRepository
from app.repositories.order_repository import OrderRepository
from app.repositories.product_repository import ProductRepository

router = APIRouter()
admin_templates = Jinja2Templates(directory="templates/admin")


@router.get("/", response_class=HTMLResponse)
async def dashboard_home(request: Request, db: Session = Depends(get_db)):
    """Main dashboard with overview stats"""
    stats = {
        "total_products": ProductRepository.count(db, active_only=False),
        "active_products": ProductRepository.count(db, active_only=True),
        "total_categories": CategoryRepository.count(db, active_only=False),
        "total_orders": OrderRepository.count(db),
        "total_users": AdminUserRepository.count(db, active_only=False),
    }

    recent_orders = OrderRepository.get_all(
        db, skip=0, limit=5, sort_by="created_at", sort_order="desc"
    )

    return admin_templates.TemplateResponse("dashboard.html", {
        "request": request,
        "stats": stats,
        "recent_orders": recent_orders
    })


# Products Routes
@router.get("/products", response_class=HTMLResponse)
async def products_page(request: Request, db: Session = Depends(get_db)):
    """Products management page"""
    categories = CategoryRepository.get_all(db, skip=0, limit=1000, active_only=True)
    return admin_templates.TemplateResponse("products.html", {
        "request": request,
        "categories": categories
    })

# ... rest of admin routes
