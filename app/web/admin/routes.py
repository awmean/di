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


