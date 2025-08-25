from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.orders.repository import OrderRepository, OrderItemRepository
from app.orders.schemas import OrderResponse, OrderItemResponse

router = APIRouter(prefix="/orders", tags=["Orders"])


@router.put("/{order_id}/status", response_model=OrderResponse)
def update_order_status(order_id: int, status: str, db: Session = Depends(get_db)):
    """Update order status"""
    if status not in ["new", "processing", "completed", "cancelled"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid status"
        )

    order = OrderRepository.update_status(db, order_id, status)
    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Order not found"
        )
    return order


@router.delete("/{order_id}")
def delete_order(order_id: int, db: Session = Depends(get_db)):
    """Delete order"""
    if not OrderRepository.delete(db, order_id):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Order not found"
        )
    return {"message": "Order deleted successfully"}


@router.get("/{order_id}/items", response_model=List[OrderItemResponse])
def get_order_items(order_id: int, db: Session = Depends(get_db)):
    """Get all items for an order"""
    # Validate order exists
    order = OrderRepository.get_by_id(db, order_id)
    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Order not found"
        )

    return OrderItemRepository.get_by_order(db=db, order_id=order_id)
