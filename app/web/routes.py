import asyncio

from fastapi import APIRouter, Request, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
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

from fastapi import Response, Depends
from sqlalchemy.orm import Session
from datetime import datetime


@router.get("/sitemap.xml")
def sitemap_index():
    """Основной sitemap-индекс"""
    xml_content = '<?xml version="1.0" encoding="UTF-8"?>\n'
    xml_content += '<sitemapindex xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'

    # Статичные страницы
    xml_content += '  <sitemap>\n'
    xml_content += '    <loc>https://luce-di-villa.ru/sitemap-static.xml</loc>\n'
    xml_content += f'    <lastmod>{datetime.now().strftime("%Y-%m-%d")}</lastmod>\n'
    xml_content += '  </sitemap>\n'

    # Товары и категории
    xml_content += '  <sitemap>\n'
    xml_content += '    <loc>https://luce-di-villa.ru/sitemap-store.xml</loc>\n'
    xml_content += f'    <lastmod>{datetime.now().strftime("%Y-%m-%d")}</lastmod>\n'
    xml_content += '  </sitemap>\n'

    xml_content += '</sitemapindex>'

    return Response(content=xml_content, media_type='application/xml')


@router.get("/sitemap-static.xml")
def sitemap_static():
    """Статичные страницы"""
    pages = []

    static_pages = [
        {'url': '/', 'priority': '1.0', 'changefreq': 'weekly'},
        {'url': '/about', 'priority': '0.7', 'changefreq': 'monthly'},
        {'url': '/contacts', 'priority': '0.8', 'changefreq': 'monthly'},
        {'url': '/payment-delivery', 'priority': '0.6', 'changefreq': 'monthly'},
        {'url': '/partnership', 'priority': '0.6', 'changefreq': 'monthly'},
        {'url': '/privacy', 'priority': '0.5', 'changefreq': 'annually'},
    ]

    for page in static_pages:
        pages.append({
            'url': f"https://luce-di-villa.ru{page['url']}",
            'lastmod': datetime.now().strftime('%Y-%m-%d'),
            'priority': page['priority'],
            'changefreq': page['changefreq']
        })

    # Генерируем XML
    xml_content = '<?xml version="1.0" encoding="UTF-8"?>\n'
    xml_content += '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'

    for page in pages:
        xml_content += '  <url>\n'
        xml_content += f'    <loc>{page["url"]}</loc>\n'
        xml_content += f'    <lastmod>{page["lastmod"]}</lastmod>\n'
        xml_content += f'    <changefreq>{page["changefreq"]}</changefreq>\n'
        xml_content += f'    <priority>{page["priority"]}</priority>\n'
        xml_content += '  </url>\n'

    xml_content += '</urlset>'

    return Response(content=xml_content, media_type='application/xml')


@router.get("/sitemap-store.xml")
def sitemap_store(db: Session = Depends(get_db)):
    """Товары и категории"""
    pages = []

    # Каталог
    pages.append({
        'url': "https://luce-di-villa.ru/catalog",
        'lastmod': datetime.now().strftime('%Y-%m-%d'),
        'priority': '0.9',
        'changefreq': 'weekly'
    })

    # Категории
    categories = CategoryRepository.get_all(db)
    for category in categories:
        pages.append({
            'url': f"https://luce-di-villa.ru/catalog/{category.slug}",
            'lastmod': datetime.now().strftime('%Y-%m-%d'),
            'priority': '0.8',
            'changefreq': 'weekly'
        })

    # Товары
    products = ProductRepository.get_all(db)
    for product in products:
        lastmod = product.updated_at.strftime('%Y-%m-%d') if hasattr(product,
                                                                     'updated_at') and product.updated_at else datetime.now().strftime(
            '%Y-%m-%d')
        pages.append({
            'url': f"https://luce-di-villa.ru/product/{product.slug}",
            'lastmod': lastmod,
            'priority': '0.7',
            'changefreq': 'monthly'
        })

    # Генерируем XML
    xml_content = '<?xml version="1.0" encoding="UTF-8"?>\n'
    xml_content += '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'

    for page in pages:
        xml_content += '  <url>\n'
        xml_content += f'    <loc>{page["url"]}</loc>\n'
        xml_content += f'    <lastmod>{page["lastmod"]}</lastmod>\n'
        xml_content += f'    <changefreq>{page["changefreq"]}</changefreq>\n'
        xml_content += f'    <priority>{page["priority"]}</priority>\n'
        xml_content += '  </url>\n'

    xml_content += '</urlset>'

    return Response(content=xml_content, media_type='application/xml')


@router.get("/robots.txt")
def robots():
    content = """User-agent: *
Allow: /

Sitemap: https://luce-di-villa.ru/sitemap.xml
Sitemap: https://luce-di-villa.ru/sitemap-static.xml
Sitemap: https://luce-di-villa.ru/sitemap-store.xml"""

    return Response(content=content, media_type='text/plain')


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


@router.get("/catalog/{category_slug}", response_class=HTMLResponse)
async def catalog_category(request: Request, category_slug: str, db: Session = Depends(get_db)):
    """Catalog page with filtering and pagination"""
    current_category = CategoryRepository.get_by_slug(db, category_slug)
    products = ProductRepository.get_all(db=db, category_id=current_category.id)
    categories = CategoryRepository.get_all(db=db)

    return templates.TemplateResponse(
        "catalog.html",
        {
            "request": request,
            "categories": categories,
            "products": products,
            'current_category': current_category,
            "current_page": 1,
        },
    )


@router.get("/payment-delivery", response_class=HTMLResponse)
async def payment_delivery(request: Request, db: Session = Depends(get_db)):
    """Catalog page with filtering and pagination"""

    return templates.TemplateResponse(
        "payment_delivery.html",
        {
            "request": request,
        },
    )


@router.get("/partnership", response_class=HTMLResponse)
async def partnership(request: Request, db: Session = Depends(get_db)):
    """Catalog page with filtering and pagination"""

    return templates.TemplateResponse(
        "partnership.html",
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
