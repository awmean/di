from fastapi import FastAPI, APIRouter, Depends
from fastapi.staticfiles import StaticFiles

# Import domain routers
from app.categories.router import router as categories_router
from app.core.auth import require_auth
from app.core.database import engine
from app.media.router import router as media_router
from app.models import Base
from app.orders.router import router as orders_router
from app.products.router import router as products_router
# Import web routers
from app.web.admin.auth_routes import router as admin_auth_router
from app.web.admin.routes import router as admin_router
from app.web.routes import router as web_router

Base.metadata.create_all(bind=engine)

app = FastAPI(title="Luce di Villa", docs_url=None, redoc_url=None, openapi_url=None)

# Static files
app.mount("/static", StaticFiles(directory="static"), name="static")
app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")

# Web routes (public)
app.include_router(web_router)

app.include_router(admin_auth_router, prefix="/admin")

# Admin web routes (защищенные) - УБИРАЕМ глобальную зависимость
app.include_router(admin_router, prefix="/admin", tags=["admin"])

# Create API router with auth dependency
api_router = APIRouter(prefix="/api", dependencies=[Depends(require_auth)])

# Add domain routers to API router
api_router.include_router(categories_router)
api_router.include_router(products_router)
api_router.include_router(orders_router)
api_router.include_router(media_router)

# Include the API router in main app
app.include_router(api_router)

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
