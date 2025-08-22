# app/api/routers/orders.py
from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.repositories.order_item import OrderItemRepository
from app.repositories.order_repository import OrderRepository
from app.repositories.product_repository import ProductRepository
from app.schemas.common import PaginatedResponse, MessageResponse
from app.schemas.filters import OrderFilters
from app.schemas.order import (
    OrderCreate, OrderUpdate, OrderResponse, OrderDetailResponse,
    OrderItemCreate, OrderItemResponse
)
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


@router.get("/", response_model=PaginatedResponse[OrderResponse])
def get_orders(
        skip: int = 0,
        limit: int = 100,
        filters: OrderFilters = Depends(),
        db: Session = Depends(get_db)
):
    """Get all orders with filters"""
    orders = OrderRepository.get_all(
        db=db,
        skip=skip,
        limit=limit,
        status=filters.status,
        customer_phone=filters.customer_phone,
        sort_by=filters.sort_by,
        sort_order=filters.sort_order
    )

    total = OrderRepository.count(db=db, status=filters.status)

    return PaginatedResponse(
        items=orders,
        total=total,
        page=(skip // limit) + 1,
        size=limit,
        pages=((total - 1) // limit) + 1 if total > 0 else 0,
        has_next=(skip + limit) < total,
        has_prev=skip > 0
    )


@router.get("/{order_id}", response_model=OrderDetailResponse)
def get_order(
        order_id: int,
        db: Session = Depends(get_db)
):
    """Get order by ID with full details"""
    order = OrderRepository.get_by_id(db, order_id)
    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Order not found"
        )
    return order


@router.put("/{order_id}", response_model=OrderResponse)
def update_order(
        order_id: int,
        order_data: OrderUpdate,
        db: Session = Depends(get_db)
):
    """Update order"""
    existing_order = OrderRepository.get_by_id(db, order_id)
    if not existing_order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Order not found"
        )

    update_data = order_data.model_dump(exclude_unset=True)
    order = OrderRepository.update(db, order_id, **update_data)
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


@router.delete("/{order_id}", response_model=MessageResponse)
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
    return MessageResponse(message="Order deleted successfully")


# Order Items endpoints
@router.post("/{order_id}/items", response_model=OrderItemResponse, status_code=status.HTTP_201_CREATED)
def add_order_item(
        order_id: int,
        item_data: OrderItemCreate,
        db: Session = Depends(get_db)
):
    """Add item to existing order"""
    # Validate order exists
    order = OrderRepository.get_by_id(db, order_id)
    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Order not found"
        )

    # Validate product exists
    product = ProductRepository.get_by_id(db, item_data.product_id)
    if not product:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Product not found"
        )

    item = OrderItemRepository.create(
        db=db,
        order_id=order_id,
        product_id=item_data.product_id,
        quantity=item_data.quantity,
        price=float(item_data.price)
    )
    return item


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


@router.put("/items/{item_id}", response_model=OrderItemResponse)
def update_order_item(
        item_id: int,
        quantity: int,
        db: Session = Depends(get_db)
):
    """Update order item quantity"""
    if quantity < 1:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Quantity must be at least 1"
        )

    item = OrderItemRepository.update_quantity(db, item_id, quantity)
    if not item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Order item not found"
        )
    return item


@router.delete("/items/{item_id}", response_model=MessageResponse)
def delete_order_item(
        item_id: int,
        db: Session = Depends(get_db)
):
    """Delete order item"""
    if not OrderItemRepository.delete(db, item_id):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Order item not found"
        )
    return MessageResponse(message="Order item deleted successfully")
