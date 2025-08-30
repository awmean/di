from datetime import datetime
from typing import Optional

from sqlalchemy import Integer, String, DateTime, ForeignKey, CheckConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from app.models import Base


class Media(Base):
    __tablename__ = "media"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    product_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("products.id", ondelete="CASCADE"), nullable=False
    )
    type: Mapped[str] = mapped_column(String(10), nullable=False)
    filename: Mapped[str] = mapped_column(String(255), nullable=False)
    original_filename: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    file_path: Mapped[str] = mapped_column(String(500), nullable=False)
    file_size: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    mime_type: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    alt_text: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)

    # Поля для разных размеров (только для изображений)
    filename_thumb: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    filename_medium: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    filename_large: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    filename_original: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)

    sort_order: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    __table_args__ = (
        CheckConstraint("type IN ('photo', 'video')", name="check_media_type"),
    )

    # Relationships
    product: Mapped["Product"] = relationship("Product", back_populates="media")

    @property
    def thumb_url(self) -> str:
        """URL миниатюры"""
        if self.type == 'photo' and self.filename_thumb:
            return f"/uploads/media/{self.filename_thumb}"
        return f"/uploads/media/{self.filename}"

    @property
    def medium_url(self) -> str:
        """URL среднего размера"""
        if self.type == 'photo' and self.filename_medium:
            return f"/uploads/media/{self.filename_medium}"
        return f"/uploads/media/{self.filename}"

    @property
    def large_url(self) -> str:
        """URL большого размера"""
        if self.type == 'photo' and self.filename_large:
            return f"/uploads/media/{self.filename_large}"
        return f"/uploads/media/{self.filename}"

    @property
    def original_url(self) -> str:
        """URL оригинального размера"""
        if self.type == 'photo' and self.filename_original:
            return f"/uploads/media/{self.filename_original}"
        return f"/uploads/media/{self.filename}"

    @property
    def responsive_srcset(self) -> str:
        """Генерирует srcset для responsive images"""
        if self.type != 'photo':
            return f"/uploads/media/{self.filename}"

        srcset_parts = []
        if self.filename_thumb:
            srcset_parts.append(f"/uploads/media/{self.filename_thumb} 300w")
        if self.filename_medium:
            srcset_parts.append(f"/uploads/media/{self.filename_medium} 800w")
        if self.filename_large:
            srcset_parts.append(f"/uploads/media/{self.filename_large} 1200w")

        return ", ".join(srcset_parts) if srcset_parts else f"/uploads/media/{self.filename}"
