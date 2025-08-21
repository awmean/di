from datetime import datetime
from decimal import Decimal
from typing import Optional, List

from sqlalchemy import Integer, String, Text, Boolean, DateTime, ForeignKey, Numeric
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from app.models import Base


class Product(Base):
    __tablename__ = "products"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    slug: Mapped[str] = mapped_column(String(200), unique=True, nullable=False, index=True)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    short_description: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)

    # Pricing
    price: Mapped[Optional[Decimal]] = mapped_column(Numeric(10, 2), index=True, nullable=True)
    old_price: Mapped[Optional[Decimal]] = mapped_column(Numeric(10, 2), nullable=True)
    sku: Mapped[Optional[str]] = mapped_column(String(50), unique=True, nullable=True)

    # Product hierarchy for sets/individual pieces
    parent_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("products.id", ondelete="CASCADE"),
                                                     nullable=True, index=True)

    # Category
    category_id: Mapped[int] = mapped_column(Integer, ForeignKey("categories.id", ondelete="RESTRICT"), nullable=False)

    # Basic characteristics
    material: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    color: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    width: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)  # in cm
    height: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)  # in cm
    depth: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)  # in cm
    weight: Mapped[Optional[Decimal]] = mapped_column(Numeric(8, 2), nullable=True)

    # Furniture-specific characteristics from your matrix
    frame_material: Mapped[Optional[str]] = mapped_column(String(200),
                                                          nullable=True)  # "Высококачественный литой алюминий + Экструзия алюминия"
    fabric_material: Mapped[Optional[str]] = mapped_column(String(200),
                                                           nullable=True)  # "100% Полиэстер", "70% Олефин 30% Полиэстер"
    fabric_density: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)  # г/м2 (200, 435, 500, etc.)
    cushion_filling: Mapped[Optional[str]] = mapped_column(Text,
                                                           nullable=True)  # "Спинка: полипропиленовый хлопок + нетканый материал..."

    # Content photos count
    content_photos_count: Mapped[Optional[int]] = mapped_column(Integer, nullable=True, default=0)

    # Set information (for parent products)
    set_piece_count: Mapped[Optional[int]] = mapped_column(Integer,
                                                           nullable=True)  # Total pieces in set (4, 6, 8, etc.)

    # Individual piece information
    piece_quantity: Mapped[Optional[int]] = mapped_column(Integer, nullable=True,
                                                          default=1)  # How many of this piece in the set

    # SEO
    meta_title: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    meta_description: Mapped[Optional[str]] = mapped_column(String(300), nullable=True)

    # Management
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, index=True)
    is_featured: Mapped[bool] = mapped_column(Boolean, default=False, index=True)
    sort_order: Mapped[int] = mapped_column(Integer, default=0)

    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now())

    # Self-referential relationship for product hierarchy
    parent: Mapped[Optional["Product"]] = relationship("Product", remote_side=[id], back_populates="children")
    children: Mapped[List["Product"]] = relationship("Product", back_populates="parent", cascade="all, delete-orphan")

    # Other relationships - use string reference for Category
    category: Mapped["Category"] = relationship("Category", back_populates="products")
    media: Mapped[List["Media"]] = relationship(
        "Media",
        back_populates="product",
        cascade="all, delete-orphan",
        order_by="Media.sort_order")
    order_items: Mapped[List["OrderItem"]] = relationship("OrderItem", back_populates="product")

    @property
    def main_image(self) -> Optional["Media"]:
        """Get the main image for this product (lowest sort_order)"""
        photos = [media_item for media_item in self.media if media_item.type == 'photo']
        if not photos:
            return None
        # Return the photo with the lowest sort_order
        return min(photos, key=lambda x: x.sort_order)

    @property
    def main_image_url(self) -> Optional[str]:
        main_img = self.main_image
        return f'/{main_img.file_path}' if main_img else None

    @property
    def images(self) -> List["Media"]:
        """Get all images for this product, sorted by sort_order"""
        photos = [media_item for media_item in self.media if media_item.type == 'photo']
        return sorted(photos, key=lambda x: x.sort_order)

    @property
    def image_urls(self) -> List[str]:
        return [f'/{img.file_path}' for img in self.images]

    @property
    def videos(self) -> List["Media"]:
        """Get all videos for this product, sorted by sort_order"""
        videos = [media_item for media_item in self.media if media_item.type == 'video']
        return sorted(videos, key=lambda x: x.sort_order)

    @property
    def is_set(self) -> bool:
        """Check if this product is a furniture set (has child products)"""
        return self.parent_id is None and len(self.children) > 0

    @property
    def is_individual_piece(self) -> bool:
        """Check if this product is an individual piece (has parent)"""
        return self.parent_id is not None

    @property
    def is_standalone_product(self) -> bool:
        """Check if this product is standalone (no parent, no children)"""
        return self.parent_id is None and len(self.children) == 0

    @property
    def has_children(self) -> bool:
        """Check if this product has child products"""
        return len(self.children) > 0

    @property
    def total_set_price(self) -> Optional[Decimal]:
        """Calculate total price of all pieces in set"""
        if not self.is_set or not self.children:
            return self.price

        total = Decimal('0')
        for child in self.children:
            if child.price and child.piece_quantity:
                total += child.price * child.piece_quantity
        return total if total > 0 else self.price

    def __repr__(self):
        return f"<Product(id={self.id}, name='{self.name}', parent_id={self.parent_id}, category='{self.category.name if self.category else None}')>"
