from datetime import datetime
from decimal import Decimal
from typing import Optional

from pydantic import BaseModel

from app.models import Category


class ProductBase(BaseModel):
    name: str
    slug: str
    description: Optional[str] = None
    short_description: Optional[str] = None
    price: Optional[Decimal] = None
    old_price: Optional[Decimal] = None
    sku: Optional[str] = None
    parent_id: Optional[int] = None
    category_id: int
    material: Optional[str] = None
    color: Optional[str] = None
    width: Optional[int] = None
    height: Optional[int] = None
    depth: Optional[int] = None
    weight: Optional[Decimal] = None
    frame_material: Optional[str] = None
    fabric_material: Optional[str] = None
    fabric_density: Optional[int] = None
    cushion_filling: Optional[str] = None
    content_photos_count: Optional[int] = 0
    set_piece_count: Optional[int] = None
    piece_quantity: Optional[int] = 1
    meta_title: Optional[str] = None
    meta_description: Optional[str] = None
    is_active: bool = True
    is_featured: bool = False
    sort_order: int = 0


class ProductCreate(ProductBase):
    pass


class ProductUpdate(ProductBase):
    pass


class Product(ProductBase):
    id: int
    created_at: datetime
    updated_at: datetime
    category: Optional[Category] = None

    class Config:
        orm_mode = True
