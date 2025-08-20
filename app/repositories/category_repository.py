from typing import List, Optional

from sqlalchemy.orm import Session

from app.models import Category


class CategoryRepository:
    @staticmethod
    def create(db: Session, name: str, slug: str, description: Optional[str] = None,
               parent_id: Optional[int] = None, sort_order: int = 0, is_active: bool = True) -> Category:
        """Create new category"""
        category = Category(
            name=name,
            slug=slug,
            description=description,
            parent_id=parent_id,
            sort_order=sort_order,
            is_active=is_active
        )
        db.add(category)
        db.commit()
        db.refresh(category)
        return category

    @staticmethod
    def get_by_id(db: Session, category_id: int) -> Optional[Category]:
        """Get category by ID"""
        return db.query(Category).filter(Category.id == category_id).first()

    @staticmethod
    def get_by_slug(db: Session, slug: str) -> Optional[Category]:
        """Get category by slug"""
        return db.query(Category).filter(Category.slug == slug).first()

    @staticmethod
    def get_all(db: Session, skip: int = 0, limit: int = 100,
                active_only: bool = False, parent_id: Optional[int] = None) -> List[Category]:
        """Get all categories with filters"""
        query = db.query(Category)

        if active_only:
            query = query.filter(Category.is_active == True)

        if parent_id is not None:
            query = query.filter(Category.parent_id == parent_id)

        return query.order_by(Category.sort_order, Category.name).offset(skip).limit(limit).all()

    @staticmethod
    def get_root_categories(db: Session, active_only: bool = False) -> List[Category]:
        """Get root categories (without parent)"""
        query = db.query(Category).filter(Category.parent_id.is_(None))

        if active_only:
            query = query.filter(Category.is_active == True)

        return query.order_by(Category.sort_order, Category.name).all()

    @staticmethod
    def update(db: Session, category_id: int, **kwargs) -> Optional[Category]:
        """Update category"""
        category = db.query(Category).filter(Category.id == category_id).first()
        if not category:
            return None

        for key, value in kwargs.items():
            if hasattr(category, key):
                setattr(category, key, value)

        db.commit()
        db.refresh(category)
        return category

    @staticmethod
    def delete(db: Session, category_id: int) -> bool:
        """Delete category"""
        category = db.query(Category).filter(Category.id == category_id).first()
        if not category:
            return False

        db.delete(category)
        db.commit()
        return True

    @staticmethod
    def count(db: Session, active_only: bool = False) -> int:
        """Count categories"""
        query = db.query(Category)
        if active_only:
            query = query.filter(Category.is_active == True)
        return query.count()
