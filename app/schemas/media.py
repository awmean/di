from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class MediaBase(BaseModel):
    type: str
    filename: str
    original_filename: Optional[str] = None
    file_path: str
    file_size: Optional[int] = None
    mime_type: Optional[str] = None
    alt_text: Optional[str] = None
    sort_order: int = 0
    is_main: bool = False


class MediaCreate(MediaBase):
    product_id: int


class MediaUpdate(MediaBase):
    pass


class Media(MediaBase):
    id: int
    created_at: datetime

    class Config:
        orm_mode = True
