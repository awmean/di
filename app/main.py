from fastapi import FastAPI, APIRouter, Depends
from fastapi.staticfiles import StaticFiles

# Import domain routers
from app.admin_users.router import router as admin_users_router
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


def create_app() -> FastAPI:
    app = FastAPI(title="Luce di Villa")

    # Static files
    app.mount("/static", StaticFiles(directory="static"), name="static")
    app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")

    # Web routes (public)
    app.include_router(web_router)
    app.include_router(admin_auth_router, prefix="/admin")

    # Admin web routes (protected)
    app.include_router(
        admin_router,
        prefix="/admin",
        tags=["admin"],
        dependencies=[Depends(require_auth)]
    )

    # Create API router with auth dependency
    api_router = APIRouter(
        prefix="/api/v1",
        dependencies=[Depends(require_auth)]
    )

    # Add domain routers to API router
    api_router.include_router(admin_users_router)
    api_router.include_router(categories_router)
    api_router.include_router(products_router)
    api_router.include_router(orders_router)
    api_router.include_router(media_router)

    # Include the API router in main app
    app.include_router(api_router)

    return app


app = create_app()

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)