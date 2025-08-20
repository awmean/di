from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel


class OrderItemBase(BaseModel):
    product_id: int
    quantity: int
    price: Decimal


class OrderItemCreate(OrderItemBase):
    pass


class OrderItemUpdate(OrderItemBase):
    pass


class OrderItem(OrderItemBase):
    id: int
    created_at: datetime

    class Config:
        orm_mode = True
