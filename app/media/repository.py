from typing import List, Optional

from sqlalchemy.orm import Session

from app.media.models import Media


class MediaRepository:
    @staticmethod
    def create(db: Session, product_id: int, type: str, filename: str,
               file_path: str, original_filename: Optional[str] = None,
               file_size: Optional[int] = None, mime_type: Optional[str] = None,
               alt_text: Optional[str] = None) -> Media:
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
            sort_order=MediaRepository.get_next_sort_order(db, product_id),
        )
        db.add(media)
        db.commit()
        db.refresh(media)
        return media

    @staticmethod
    def get_next_sort_order(db: Session, product_id: int) -> Optional[int]:
        media: Optional[Media] = db.query(Media).filter(
            Media.product_id == product_id,
        ).order_by(Media.sort_order.desc()).first()

        if not media:
            return 0

        return media.sort_order + 1

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

        return query.order_by(Media.sort_order.asc()).all()

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
