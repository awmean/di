from typing import List, Optional

from sqlalchemy import and_, or_, desc, asc
from sqlalchemy.orm import Session

from app.products.models import Product


class ProductRepository:
    @staticmethod
    def create(
        db: Session,
        name: str,
        slug: str,
        category_id: int,
        price: float,
        description: Optional[str] = None,
        short_description: Optional[str] = None,
        old_price: Optional[float] = None,
        sku: Optional[str] = None,
        **kwargs,
    ) -> Product:
        """Create new product"""
        product_data = {
            "name": name,
            "slug": slug,
            "category_id": category_id,
            "price": price,
            "description": description,
            "short_description": short_description,
            "old_price": old_price,
            "sku": sku,
        }
        product_data.update(kwargs)

        product = Product(**product_data)
        db.add(product)
        db.commit()
        db.refresh(product)
        return product

    @staticmethod
    def get_by_id(db: Session, product_id: int) -> Optional[Product]:
        """Get product by ID"""
        return db.query(Product).filter(Product.id == product_id).first()

    @staticmethod
    def get_by_slug(db: Session, slug: str) -> Optional[Product]:
        """Get product by slug"""
        return db.query(Product).filter(Product.slug == slug).first()

    @staticmethod
    def get_by_sku(db: Session, sku: str) -> Optional[Product]:
        """Get product by SKU"""
        return db.query(Product).filter(Product.sku == sku).first()

    @staticmethod
    def get_all(
        db: Session,
        skip: int = 0,
        limit: int = 100,
        active_only: bool = False,
        category_id: Optional[int] = None,
        featured_only: bool = False,
        search: Optional[str] = None,
        min_price: Optional[float] = None,
        max_price: Optional[float] = None,
        sort_by: str = "name",
        sort_order: str = "asc",
    ) -> List[Product]:
        """Get all products with filters"""
        query = db.query(Product)

        if active_only:
            query = query.filter(Product.is_active == True)

        if category_id:
            query = query.filter(Product.category_id == category_id)

        if featured_only:
            query = query.filter(Product.is_featured == True)

        if search:
            search_term = f"%{search}%"
            query = query.filter(
                or_(
                    Product.name.ilike(search_term),
                    Product.description.ilike(search_term),
                    Product.short_description.ilike(search_term),
                )
            )

        if min_price is not None:
            query = query.filter(Product.price >= min_price)

        if max_price is not None:
            query = query.filter(Product.price <= max_price)

        # Sorting
        order_column = getattr(Product, sort_by, Product.name)
        if sort_order.lower() == "desc":
            query = query.order_by(desc(order_column))
        else:
            query = query.order_by(asc(order_column))

        return query.offset(skip).limit(limit).all()

    @staticmethod
    def get_featured(db: Session, limit: int = 10) -> List[Product]:
        """Get featured products"""
        return (
            db.query(Product)
            .filter(and_(Product.is_featured == True, Product.is_active == True))
            .order_by(Product.sort_order, Product.name)
            .limit(limit)
            .all()
        )

    @staticmethod
    def update(db: Session, product_id: int, **kwargs) -> Optional[Product]:
        """Update product"""
        product = db.query(Product).filter(Product.id == product_id).first()
        if not product:
            return None

        for key, value in kwargs.items():
            if hasattr(product, key):
                setattr(product, key, value)

        db.commit()
        db.refresh(product)
        return product

    @staticmethod
    def delete(db: Session, product_id: int) -> bool:
        """Delete product"""
        product = db.query(Product).filter(Product.id == product_id).first()
        if not product:
            return False

        db.delete(product)
        db.commit()
        return True

    @staticmethod
    def count(
        db: Session, active_only: bool = False, category_id: Optional[int] = None
    ) -> int:
        """Count products"""
        query = db.query(Product)

        if active_only:
            query = query.filter(Product.is_active == True)

        if category_id:
            query = query.filter(Product.category_id == category_id)

        return query.count()
