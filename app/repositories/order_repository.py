from typing import List, Optional

from sqlalchemy import desc, asc, func
from sqlalchemy.orm import Session

from app.models import Order
from app.models import OrderItem


class OrderRepository:
    @staticmethod
    def create(db: Session, customer_name: str, customer_phone: str,
               comment: Optional[str] = None, status: str = "new") -> Order:
        """Create new order"""
        order = Order(
            customer_name=customer_name,
            customer_phone=customer_phone,
            comment=comment,
            status=status,
            total_amount=0
        )
        db.add(order)
        db.commit()
        db.refresh(order)
        return order

    @staticmethod
    def get_by_id(db: Session, order_id: int) -> Optional[Order]:
        """Get order by ID"""
        return db.query(Order).filter(Order.id == order_id).first()

    @staticmethod
    def get_all(db: Session, skip: int = 0, limit: int = 100,
                status: Optional[str] = None, customer_phone: Optional[str] = None,
                sort_by: str = 'created_at', sort_order: str = 'desc') -> List[Order]:
        """Get all orders with filters"""
        query = db.query(Order)

        if status:
            query = query.filter(Order.status == status)

        if customer_phone:
            query = query.filter(Order.customer_phone.ilike(f"%{customer_phone}%"))

        # Sorting
        order_column = getattr(Order, sort_by, Order.created_at)
        if sort_order.lower() == 'desc':
            query = query.order_by(desc(order_column))
        else:
            query = query.order_by(asc(order_column))

        return query.offset(skip).limit(limit).all()

    @staticmethod
    def update_status(db: Session, order_id: int, status: str) -> Optional[Order]:
        """Update order status"""
        order = db.query(Order).filter(Order.id == order_id).first()
        if not order:
            return None

        order.status = status
        db.commit()
        db.refresh(order)
        return order

    @staticmethod
    def update(db: Session, order_id: int, **kwargs) -> Optional[Order]:
        """Update order"""
        order = db.query(Order).filter(Order.id == order_id).first()
        if not order:
            return None

        for key, value in kwargs.items():
            if hasattr(order, key):
                setattr(order, key, value)

        db.commit()
        db.refresh(order)
        return order

    @staticmethod
    def delete(db: Session, order_id: int) -> bool:
        """Delete order"""
        order = db.query(Order).filter(Order.id == order_id).first()
        if not order:
            return False

        db.delete(order)
        db.commit()
        return True

    @staticmethod
    def calculate_total(db: Session, order_id: int) -> float:
        """Calculate and update order total"""
        total = db.query(OrderItem).filter(OrderItem.order_id == order_id).with_entities(
            func.sum(OrderItem.price * OrderItem.quantity)
        ).scalar() or 0

        order = db.query(Order).filter(Order.id == order_id).first()
        if order:
            order.total_amount = total
            db.commit()

        return total

    @staticmethod
    def count(db: Session, status: Optional[str] = None) -> int:
        """Count orders"""
        query = db.query(Order)
        if status:
            query = query.filter(Order.status == status)
        return query.count()
