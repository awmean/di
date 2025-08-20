from datetime import datetime
from decimal import Decimal
from typing import Optional, List

from pydantic import BaseModel

from app.schemas.order_item import OrderItemCreate, OrderItemUpdate, OrderItem


class OrderBase(BaseModel):
    customer_name: str
    customer_phone: str
    comment: Optional[str] = None
    status: str = "new"
    total_amount: Optional[Decimal] = None


class OrderCreate(OrderBase):
    items: List[OrderItemCreate]


class OrderUpdate(OrderBase):
    items: Optional[List[OrderItemUpdate]] = None


class Order(OrderBase):
    id: int
    created_at: datetime
    updated_at: datetime
    items: List[OrderItem] = []

    class Config:
        orm_mode = True
