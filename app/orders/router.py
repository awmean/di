from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.orders.repository import OrderRepository, OrderItemRepository
from app.orders.schemas import OrderResponse, OrderCreate, OrderItemResponse
from app.products.repository import ProductRepository
from app.telegram import TelegramMessenger

router = APIRouter(prefix="/orders", tags=["Orders"])


@router.post("/", response_model=OrderResponse, status_code=status.HTTP_201_CREATED)
def create_order(
        order_data: OrderCreate,
        db: Session = Depends(get_db)
):
    """Create new order with items"""
    # Validate all products exist
    for item in order_data.items:
        product = ProductRepository.get_by_id(db, item.product_id)
        if not product:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Product with ID {item.product_id} not found"
            )

    # Create order
    order = OrderRepository.create(
        db=db,
        customer_name=order_data.customer_name,
        customer_phone=order_data.customer_phone,
        comment=order_data.comment,
        status=order_data.status
    )

    # Create order items
    for item_data in order_data.items:
        OrderItemRepository.create(
            db=db,
            order_id=order.id,
            product_id=item_data.product_id,
            quantity=item_data.quantity,
            price=float(item_data.price)
        )

    # Refresh order to get items and updated total
    db.refresh(order)

    TelegramMessenger.send_order(order)
    return order


@router.put("/{order_id}/status", response_model=OrderResponse)
def update_order_status(
        order_id: int,
        status: str,
        db: Session = Depends(get_db)
):
    """Update order status"""
    if status not in ["new", "processing", "completed", "cancelled"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid status"
        )

    order = OrderRepository.update_status(db, order_id, status)
    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Order not found"
        )
    return order


@router.delete("/{order_id}")
def delete_order(
        order_id: int,
        db: Session = Depends(get_db)
):
    """Delete order"""
    if not OrderRepository.delete(db, order_id):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Order not found"
        )
    return {"message": "Order deleted successfully"}


@router.get("/{order_id}/items", response_model=List[OrderItemResponse])
def get_order_items(
        order_id: int,
        db: Session = Depends(get_db)
):
    """Get all items for an order"""
    # Validate order exists
    order = OrderRepository.get_by_id(db, order_id)
    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Order not found"
        )

    return OrderItemRepository.get_by_order(db=db, order_id=order_id)
