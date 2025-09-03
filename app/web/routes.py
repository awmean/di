import asyncio

from fastapi import APIRouter, Request, Depends, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from starlette import status

from app.categories.repository import CategoryRepository
from app.core.database import get_db
from app.core.formatters import format_text
from app.customers.repository import CustomersRepository
from app.customers.schemas import CustomerCreate
from app.orders.repository import OrderRepository, OrderItemRepository
from app.orders.schemas import OrderResponse, OrderCreate
from app.products.repository import ProductRepository
from app.telegram.messenger import TelegramMessenger

router = APIRouter(tags=["Web"])
templates = Jinja2Templates(directory="templates")
templates.env.filters['format_desc'] = format_text

PRODUCTS_PER_PAGE = 36


@router.get("/", response_class=HTMLResponse)
async def index(request: Request, db: Session = Depends(get_db)):
    """Homepage with categories"""
    categories = CategoryRepository.get_root_categories(db, active_only=True)[:8]
    products = ProductRepository.get_all(db, category_id=CategoryRepository.get_by_slug(db, 'sets').id)
    return templates.TemplateResponse(
        "index.html", {"request": request, "categories": categories, 'products': products}
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
        },
    )


@router.get("/payment-delivery", response_class=HTMLResponse)
async def catalog(request: Request, db: Session = Depends(get_db)):
    """Catalog page with filtering and pagination"""

    return templates.TemplateResponse(
        "payment_delivery.html",
        {
            "request": request,
        },
    )


@router.get("/product/{slug}", response_class=HTMLResponse)
async def catalog(request: Request, slug: str, db: Session = Depends(get_db)):
    """Catalog page with filtering and pagination"""
    product = ProductRepository.get_by_slug(db=db, slug=slug)

    return templates.TemplateResponse(
        "product.html", {"request": request, "product": product}
    )


@router.get("/catalog/{category_slug}", response_class=HTMLResponse)
async def category_detail(
        category_slug: str, request: Request, db: Session = Depends(get_db)
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
            "products": category.products,
        },
    )


@router.post(
    '/customer-create', status_code=status.HTTP_201_CREATED
)
async def create_customer(customer_data: CustomerCreate, db: Session = Depends(get_db)):
    customer = CustomersRepository.create(db, **customer_data.model_dump())
    asyncio.create_task(TelegramMessenger.send_customer(customer))

    return {'success': True}


@router.post(
    "/order", response_model=OrderResponse, status_code=status.HTTP_201_CREATED
)
async def create_order(order_data: OrderCreate, db: Session = Depends(get_db)):
    """Create new order with items"""
    # Validate all products exist
    for item in order_data.items:
        product = ProductRepository.get_by_id(db, item.product_id)
        if not product:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Product with ID {item.product_id} not found",
            )

    # Create order
    order = OrderRepository.create(
        db=db,
        customer_name=order_data.customer_name,
        customer_phone=order_data.customer_phone,
        comment=order_data.comment,
        status=order_data.status,
    )

    # Create order items
    for item_data in order_data.items:
        OrderItemRepository.create(
            db=db,
            order_id=order.id,
            product_id=item_data.product_id,
            quantity=item_data.quantity,
            price=float(item_data.price),
        )

    # Refresh order to get items and updated total
    db.refresh(order)

    asyncio.create_task(TelegramMessenger.send_order(order))

    return order


@router.get("/about", response_class=HTMLResponse)
async def about(request: Request):
    """About page"""
    return templates.TemplateResponse("about.html", {"request": request})


@router.get("/checkout", response_class=HTMLResponse)
async def checkout(request: Request):
    """About page"""
    return templates.TemplateResponse("checkout.html", {"request": request})


@router.get("/contacts", response_class=HTMLResponse)
async def contacts(request: Request):
    """Contacts page"""
    return templates.TemplateResponse("contacts.html", {"request": request})


@router.get("/privacy", response_class=HTMLResponse)
async def privacy(request: Request):
    """Contacts page"""
    return templates.TemplateResponse("privacy.html", {"request": request})
