from typing import List, Optional

from sqlalchemy.orm import Session

from app.repositories.order_repository import OrderRepository
from app.models import OrderItem


class OrderItemRepository:
    @staticmethod
    def create(db: Session, order_id: int, product_id: int,
               quantity: int, price: float) -> OrderItem:
        """Create new order item"""
        item = OrderItem(
            order_id=order_id,
            product_id=product_id,
            quantity=quantity,
            price=price
        )
        db.add(item)
        db.commit()
        db.refresh(item)

        # Update order total
        OrderRepository.calculate_total(db, order_id)

        return item

    @staticmethod
    def get_by_id(db: Session, item_id: int) -> Optional[OrderItem]:
        """Get order item by ID"""
        return db.query(OrderItem).filter(OrderItem.id == item_id).first()

    @staticmethod
    def get_by_order(db: Session, order_id: int) -> List[OrderItem]:
        """Get all items for an order"""
        return db.query(OrderItem).filter(OrderItem.order_id == order_id).all()

    @staticmethod
    def update(db: Session, item_id: int, **kwargs) -> Optional[OrderItem]:
        """Update order item"""
        item = db.query(OrderItem).filter(OrderItem.id == item_id).first()
        if not item:
            return None

        for key, value in kwargs.items():
            if hasattr(item, key):
                setattr(item, key, value)

        db.commit()
        db.refresh(item)

        # Update order total
        OrderRepository.calculate_total(db, item.order_id)

        return item

    @staticmethod
    def delete(db: Session, item_id: int) -> bool:
        """Delete order item"""
        item = db.query(OrderItem).filter(OrderItem.id == item_id).first()
        if not item:
            return False

        order_id = item.order_id
        db.delete(item)
        db.commit()

        # Update order total
        OrderRepository.calculate_total(db, order_id)

        return True

    @staticmethod
    def update_quantity(db: Session, item_id: int, quantity: int) -> Optional[OrderItem]:
        """Update item quantity"""
        item = db.query(OrderItem).filter(OrderItem.id == item_id).first()
        if not item:
            return None

        item.quantity = quantity
        db.commit()
        db.refresh(item)

        # Update order total
        OrderRepository.calculate_total(db, item.order_id)

        return item
