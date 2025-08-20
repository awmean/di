import re
from datetime import datetime
from decimal import Decimal
from typing import Optional, List

from pydantic import BaseModel, Field, validator

from .category import CategoryResponse
from .media import MediaResponse


class ProductBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=200, description="Product name")
    slug: str = Field(..., max_length=200, description="URL slug")
    description: Optional[str] = Field(None, description="Full description")
    short_description: Optional[str] = Field(None, max_length=500, description="Short description")

    # Pricing
    price: Optional[Decimal] = Field(None, ge=0, decimal_places=2, description="Product price")
    old_price: Optional[Decimal] = Field(None, ge=0, decimal_places=2, description="Old price for discounts")
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
    weight: Optional[Decimal] = Field(None, ge=0, decimal_places=2, description="Weight")

    # Furniture-specific
    frame_material: Optional[str] = Field(None, max_length=200, description="Frame material")
    fabric_material: Optional[str] = Field(None, max_length=200, description="Fabric material")
    fabric_density: Optional[int] = Field(None, ge=0, description="Fabric density in g/m²")
    cushion_filling: Optional[str] = Field(None, description="Cushion filling description")

    # Set information
    set_piece_count: Optional[int] = Field(None, ge=1, description="Total pieces in set")
    piece_quantity: Optional[int] = Field(default=1, ge=1, description="Quantity of this piece in set")
    content_photos_count: Optional[int] = Field(default=0, ge=0, description="Number of content photos")

    # SEO
    meta_title: Optional[str] = Field(None, max_length=200, description="Meta title")
    meta_description: Optional[str] = Field(None, max_length=300, description="Meta description")

    # Management
    is_active: bool = Field(default=True, description="Whether product is active")
    is_featured: bool = Field(default=False, description="Whether product is featured")
    sort_order: int = Field(default=0, description="Sort order")

    @validator('slug')
    def validate_slug(cls, v):
        if not re.match(r'^[a-z0-9-]+$', v):
            raise ValueError('Slug can only contain lowercase letters, numbers, and hyphens')
        return v

    @validator('old_price')
    def validate_old_price(cls, v, values):
        if v is not None and 'price' in values and values['price'] is not None:
            if v <= values['price']:
                raise ValueError('Old price must be greater than current price')
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

    @validator('slug')
    def validate_slug(cls, v):
        if v is not None and not re.match(r'^[a-z0-9-]+$', v):
            raise ValueError('Slug can only contain lowercase letters, numbers, and hyphens')
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
    is_standalone_product: bool = Field(description="Whether this is a standalone product")
    has_children: bool = Field(description="Whether this product has child products")
    total_set_price: Optional[Decimal] = Field(description="Total price of all pieces in set")

    class Config:
        from_attributes = True


class ProductDetailResponse(ProductResponse):
    """Extended product response with children and parent"""
    children: List[ProductResponse] = []
    parent: Optional[ProductResponse] = None


class ProductListResponse(BaseModel):
    """Simplified product response for lists"""
    id: int
    name: str
    slug: str
    short_description: Optional[str]
    price: Optional[Decimal]
    old_price: Optional[Decimal]
    is_featured: bool
    main_image: Optional[str] = Field(None, description="Main image URL")
    category_name: str
    is_set: bool

    class Config:
        from_attributes = True


class ProductSetResponse(ProductResponse):
    """Response for furniture sets with all pieces"""
    pieces: List[ProductResponse] = Field(description="Individual pieces in the set")
