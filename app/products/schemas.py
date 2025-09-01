import re
from datetime import datetime
from decimal import Decimal
from decimal import InvalidOperation
from typing import List
from typing import Optional

from pydantic import BaseModel, Field, field_validator
from pydantic import validator

from app.categories.schemas import CategoryResponse
from app.media.schemas import MediaResponse


class ProductBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=200, description="Product name")
    slug: str = Field(..., max_length=200, description="URL slug")
    description: Optional[str] = Field(None, description="Full description")
    short_description: Optional[str] = Field(
        None, max_length=500, description="Short description"
    )

    # Pricing
    price: Optional[Decimal] = Field(
        None, ge=0, decimal_places=2, description="Product price"
    )
    old_price: Optional[Decimal] = Field(
        None, ge=0, decimal_places=2, description="Old price for discounts"
    )
    sku: Optional[str] = Field(None, max_length=50, description="Stock keeping unit")

    # Hierarchy
    parent_id: Optional[int] = Field(None, description="Parent product ID for sets")
    category_id: int = Field(..., description="Category ID")

    # Basic characteristics
    material: Optional[str] = Field(None, max_length=100, description="Material")
    color: Optional[str] = Field(None, max_length=50, description="Color")
    width: Optional[int] = Field(None, ge=0, description="Width in cm")
    height: Optional[int] = Field(None, ge=0, description="Height in cm")
    depth: Optional[int] = Field(None, ge=0, description="Depth in cm")
    weight: Optional[Decimal] = Field(
        None, ge=0, decimal_places=2, description="Weight"
    )

    # Furniture-specific
    frame_material: Optional[str] = Field(
        None, max_length=200, description="Frame material"
    )
    fabric_material: Optional[str] = Field(
        None, max_length=200, description="Fabric material"
    )
    fabric_density: Optional[int] = Field(
        None, ge=0, description="Fabric density in g/m²"
    )
    cushion_filling: Optional[str] = Field(
        None, description="Cushion filling description"
    )

    # Set information
    set_piece_count: Optional[int] = Field(
        None, ge=1, description="Total pieces in set"
    )
    piece_quantity: Optional[int] = Field(
        default=1, ge=1, description="Quantity of this piece in set"
    )
    content_photos_count: Optional[int] = Field(
        default=0, ge=0, description="Number of content photos"
    )

    # SEO
    meta_title: Optional[str] = Field(None, max_length=200, description="Meta title")
    meta_description: Optional[str] = Field(
        None, max_length=300, description="Meta description"
    )

    # Management
    is_active: bool = Field(default=True, description="Whether product is active")
    is_featured: bool = Field(default=False, description="Whether product is featured")
    sort_order: int = Field(default=0, description="Sort order")

    # Field validators to handle empty strings from forms
    @field_validator('price', 'old_price', 'weight', mode='before')
    @classmethod
    def parse_decimal_or_none(cls, v):
        if v == '' or v is None:
            return None
        try:
            return Decimal(str(v))
        except (ValueError, TypeError, InvalidOperation):
            raise ValueError('Must be a valid decimal number or empty')

    @field_validator(
        'parent_id', 'width', 'height', 'depth', 'fabric_density',
        'set_piece_count', 'piece_quantity', 'content_photos_count',
        'sort_order', mode='before'
    )
    @classmethod
    def parse_int_or_none(cls, v):
        if v == '' or v is None:
            return None
        try:
            return int(v)
        except (ValueError, TypeError):
            raise ValueError('Must be a valid integer or empty')

    @field_validator(
        'description', 'short_description', 'sku', 'material', 'color',
        'frame_material', 'fabric_material', 'cushion_filling',
        'meta_title', 'meta_description', mode='before'
    )
    @classmethod
    def empty_str_to_none(cls, v):
        if v == '':
            return None
        return v

    @field_validator("slug")
    @classmethod
    def validate_slug(cls, v):
        if not re.match(r"^[a-z0-9-]+$", v):
            raise ValueError(
                "Slug can only contain lowercase letters, numbers, and hyphens"
            )
        return v

    @field_validator("old_price")
    @classmethod
    def validate_old_price(cls, v, info):
        if v is not None and info.data.get("price") is not None:
            if v <= info.data["price"]:
                raise ValueError("Old price must be greater than current price")
        return v


class ProductCreate(ProductBase):
    pass


class ProductUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=200)
    slug: Optional[str] = Field(None, max_length=200)
    description: Optional[str] = None
    short_description: Optional[str] = Field(None, max_length=500)
    price: Optional[Decimal] = Field(None, ge=0, decimal_places=2)
    old_price: Optional[Decimal] = Field(None, ge=0, decimal_places=2)
    sku: Optional[str] = Field(None, max_length=50)
    parent_id: Optional[int] = None
    category_id: Optional[int] = None
    material: Optional[str] = Field(None, max_length=100)
    color: Optional[str] = Field(None, max_length=50)
    width: Optional[int] = Field(None, ge=0)
    height: Optional[int] = Field(None, ge=0)
    depth: Optional[int] = Field(None, ge=0)
    weight: Optional[Decimal] = Field(None, ge=0, decimal_places=2)
    frame_material: Optional[str] = Field(None, max_length=200)
    fabric_material: Optional[str] = Field(None, max_length=200)
    fabric_density: Optional[int] = Field(None, ge=0)
    cushion_filling: Optional[str] = None
    set_piece_count: Optional[int] = Field(None, ge=1)
    piece_quantity: Optional[int] = Field(None, ge=1)
    content_photos_count: Optional[int] = Field(None, ge=0)
    meta_title: Optional[str] = Field(None, max_length=200)
    meta_description: Optional[str] = Field(None, max_length=300)
    is_active: Optional[bool] = None
    is_featured: Optional[bool] = None
    sort_order: Optional[int] = None

    @validator("slug")
    def validate_slug(cls, v):
        if v is not None and not re.match(r"^[a-z0-9-]+$", v):
            raise ValueError(
                "Slug can only contain lowercase letters, numbers, and hyphens"
            )
        return v


class ProductResponse(ProductBase):
    id: int
    created_at: datetime
    updated_at: datetime
    category: CategoryResponse
    media: List[MediaResponse] = []

    # Computed properties
    is_set: bool = Field(description="Whether this is a furniture set")
    is_individual_piece: bool = Field(description="Whether this is an individual piece")
    is_standalone_product: bool = Field(
        description="Whether this is a standalone product"
    )
    has_children: bool = Field(description="Whether this product has child products")
    total_set_price: Optional[Decimal] = Field(
        description="Total price of all pieces in set"
    )

    class Config:
        from_attributes = True
