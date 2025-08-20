from fastapi import APIRouter, Request, Depends
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.repositories.category_repository import CategoryRepository
from app.repositories.product_repository import ProductRepository

router = APIRouter()
templates = Jinja2Templates(directory="templates")

PRODUCTS_PER_PAGE = 36


@router.get("/", response_class=HTMLResponse)
async def index(request: Request, db: Session = Depends(get_db)):
    """Homepage with categories"""
    categories = CategoryRepository.get_root_categories(db, active_only=True)[:8]
    return templates.TemplateResponse(
        "index.html",
        {"request": request, "categories": categories}
    )


@router.get("/catalog", response_class=HTMLResponse)
async def catalog(request: Request, db: Session = Depends(get_db)):
    """Catalog page with filtering and pagination"""
    products = ProductRepository.get_all(db=db)
    categories = CategoryRepository.get_all(db=db)

    return templates.TemplateResponse(
        "catalog.html",
        {
            "request": request,
            "categories": categories,
            "products": products,
            "current_page": 1,
        }
    )


@router.get("/catalog/{category_slug}", response_class=HTMLResponse)
async def category_detail(
        category_slug: str,
        request: Request,
        db: Session = Depends(get_db)
):
    """Category detail page with products"""
    category = CategoryRepository.get_by_slug(db, category_slug)
    if not category:
        raise HTTPException(status_code=404, detail="Category not found")

    subcategories = CategoryRepository.get_all(
        db, active_only=True, parent_id=category.id
    )

    return templates.TemplateResponse(
        "category_detail.html",
        {
            "request": request,
            "category": category,
            "subcategories": subcategories,
            "products": category.products
        }
    )


@router.get("/about", response_class=HTMLResponse)
async def about(request: Request):
    """About page"""
    return templates.TemplateResponse("about.html", {"request": request})


@router.get("/contacts", response_class=HTMLResponse)
async def contacts(request: Request):
    """Contacts page"""
    return templates.TemplateResponse("contacts.html", {"request": request})


@router.post("/subscribe")
async def subscribe(phone: str, db: Session = Depends(get_db)):
    """Handle newsletter subscription"""
    # TODO: Implement subscription logic
    return {"message": "Спасибо! Мы свяжемся с вами."}
