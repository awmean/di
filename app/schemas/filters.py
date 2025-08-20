from datetime import datetime
from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, Field


class ProductFilters(BaseModel):
    """Filters for product listing"""
    category_id: Optional[int] = Field(None, description="Filter by category")
    is_active: Optional[bool] = Field(None, description="Filter by active status")
    is_featured: Optional[bool] = Field(None, description="Filter by featured status")
    is_set: Optional[bool] = Field(None, description="Filter by set products")
    min_price: Optional[Decimal] = Field(None, ge=0, description="Minimum price")
    max_price: Optional[Decimal] = Field(None, ge=0, description="Maximum price")
    material: Optional[str] = Field(None, description="Filter by material")
    color: Optional[str] = Field(None, description="Filter by color")
    search: Optional[str] = Field(None, min_length=1, description="Search in name and description")

    # Sorting
    sort_by: Optional[str] = Field("created_at", pattern="^(name|price|created_at|updated_at|sort_order)$")
    sort_order: Optional[str] = Field("desc", pattern="^(asc|desc)$")


class CategoryFilters(BaseModel):
    """Filters for category listing"""
    parent_id: Optional[int] = Field(None, description="Filter by parent category")
    is_active: Optional[bool] = Field(None, description="Filter by active status")
    search: Optional[str] = Field(None, min_length=1, description="Search in name and description")
    sort_by: Optional[str] = Field("sort_order", pattern="^(name|created_at|sort_order)$")
    sort_order: Optional[str] = Field("asc", pattern="^(asc|desc)$")


class OrderFilters(BaseModel):
    """Filters for order listing"""
    status: Optional[str] = Field(None, pattern="^(new|processing|completed|cancelled)$")
    customer_name: Optional[str] = Field(None, description="Filter by customer name")
    customer_phone: Optional[str] = Field(None, description="Filter by customer phone")
    date_from: Optional[datetime] = Field(None, description="Filter orders from this date")
    date_to: Optional[datetime] = Field(None, description="Filter orders to this date")
    sort_by: Optional[str] = Field("created_at", pattern="^(created_at|updated_at|total_amount)$")
    sort_order: Optional[str] = Field("desc", pattern="^(asc|desc)$")
