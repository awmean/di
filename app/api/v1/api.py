from fastapi import APIRouter

from app.api.v1.endpoints import admin_users, categories, media, orders, products

api_router = APIRouter()

api_router.include_router(admin_users.router)
api_router.include_router(categories.router)
api_router.include_router(media.router)
api_router.include_router(orders.router)
api_router.include_router(products.router)
