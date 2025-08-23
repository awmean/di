from datetime import datetime
from decimal import Decimal
from typing import Optional, List

from pydantic import BaseModel, Field, validator


class OrderItemBase(BaseModel):
    product_id: int = Field(..., description="Product ID")
    quantity: int = Field(..., ge=1, description="Quantity")
    price: Decimal = Field(..., ge=0, decimal_places=2, description="Price per item")


class OrderItemCreate(OrderItemBase):
    pass


class OrderItemResponse(OrderItemBase):
    id: int
    order_id: int
    created_at: datetime

    # You might want to include product details here
    # product: ProductListResponse

    class Config:
        from_attributes = True


class OrderBase(BaseModel):
    customer_name: str = Field(..., min_length=1, max_length=100, description="Customer name")
    customer_phone: str = Field(..., min_length=1, max_length=20, description="Customer phone")
    comment: Optional[str] = Field(None, description="Order comment")
    status: str = Field(default="new", pattern="^(new|processing|completed|cancelled)$", description="Order status")


class OrderCreate(OrderBase):
    items: List[OrderItemCreate] = Field(..., min_items=1, description="Order items")

    @validator('items')
    def validate_items(cls, v):
        if not v:
            raise ValueError('Order must have at least one item')
        return v


class OrderUpdate(BaseModel):
    customer_name: Optional[str] = Field(None, min_length=1, max_length=100)
    customer_phone: Optional[str] = Field(None, min_length=1, max_length=20)
    comment: Optional[str] = None
    status: Optional[str] = Field(None, pattern="^(new|processing|completed|cancelled)$")


class OrderResponse(OrderBase):
    id: int
    total_amount: Optional[Decimal] = Field(description="Total order amount")
    created_at: datetime
    updated_at: datetime
    items: List[OrderItemResponse] = []

    class Config:
        from_attributes = True


class OrderDetailResponse(OrderResponse):
    """Extended order response with full item details"""
    pass  # You can extend this to include full product details in items
