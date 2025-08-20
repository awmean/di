from typing import List, Optional

from sqlalchemy import and_
from sqlalchemy.orm import Session

from app.models import Media


class MediaRepository:
    @staticmethod
    def create(db: Session, product_id: int, type: str, filename: str,
               file_path: str, original_filename: Optional[str] = None,
               file_size: Optional[int] = None, mime_type: Optional[str] = None,
               alt_text: Optional[str] = None, sort_order: int = 0,
               is_main: bool = False) -> Media:
        """Create new media"""
        media = Media(
            product_id=product_id,
            type=type,
            filename=filename,
            original_filename=original_filename,
            file_path=file_path,
            file_size=file_size,
            mime_type=mime_type,
            alt_text=alt_text,
            sort_order=sort_order,
            is_main=is_main
        )
        db.add(media)
        db.commit()
        db.refresh(media)
        return media

    @staticmethod
    def get_by_id(db: Session, media_id: int) -> Optional[Media]:
        """Get media by ID"""
        return db.query(Media).filter(Media.id == media_id).first()

    @staticmethod
    def get_by_product(db: Session, product_id: int, type: Optional[str] = None) -> List[Media]:
        """Get media by product ID"""
        query = db.query(Media).filter(Media.product_id == product_id)

        if type:
            query = query.filter(Media.type == type)

        return query.order_by(Media.is_main.desc(), Media.sort_order).all()

    @staticmethod
    def get_main_image(db: Session, product_id: int) -> Optional[Media]:
        """Get main image for product"""
        return db.query(Media).filter(
            and_(
                Media.product_id == product_id,
                Media.type == 'photo',
                Media.is_main == True
            )
        ).first()

    @staticmethod
    def update(db: Session, media_id: int, **kwargs) -> Optional[Media]:
        """Update media"""
        media = db.query(Media).filter(Media.id == media_id).first()
        if not media:
            return None

        for key, value in kwargs.items():
            if hasattr(media, key):
                setattr(media, key, value)

        db.commit()
        db.refresh(media)
        return media

    @staticmethod
    def delete(db: Session, media_id: int) -> bool:
        """Delete media"""
        media = db.query(Media).filter(Media.id == media_id).first()
        if not media:
            return False

        db.delete(media)
        db.commit()
        return True

    @staticmethod
    def set_main_image(db: Session, product_id: int, media_id: int) -> bool:
        """Set main image for product"""
        # Remove main flag from all product images
        db.query(Media).filter(
            and_(Media.product_id == product_id, Media.type == 'photo')
        ).update({'is_main': False})

        # Set new main image
        media = db.query(Media).filter(Media.id == media_id).first()
        if not media or media.product_id != product_id:
            return False

        media.is_main = True
        db.commit()
        return True
