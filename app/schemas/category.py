from datetime import datetime
from typing import Optional, List

from pydantic import BaseModel


class CategoryMediaBase(BaseModel):
    type: str
    filename: str
    original_filename: Optional[str] = None
    file_path: str
    file_size: Optional[int] = None
    mime_type: Optional[str] = None
    alt_text: Optional[str] = None
    sort_order: int = 0
    is_main: bool = False


class CategoryMediaCreate(CategoryMediaBase):
    category_id: int


class CategoryMedia(CategoryMediaBase):
    id: int
    created_at: datetime

    class Config:
        orm_mode = True


class CategoryBase(BaseModel):
    name: str
    slug: str
    description: Optional[str] = None
    parent_id: Optional[int] = None
    sort_order: int = 0
    is_active: bool = True


class CategoryCreate(CategoryBase):
    pass


class CategoryUpdate(CategoryBase):
    pass


class Category(CategoryBase):
    id: int
    created_at: datetime
    updated_at: datetime
    media: List[CategoryMedia] = []

    class Config:
        orm_mode = True
