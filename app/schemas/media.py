from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class MediaBase(BaseModel):
    type: str = Field(..., pattern="^(photo|video)$", description="Media type")
    filename: str = Field(..., max_length=255, description="File name")
    original_filename: Optional[str] = Field(None, max_length=255, description="Original file name")
    file_path: str = Field(..., max_length=500, description="File path")
    file_size: Optional[int] = Field(None, ge=0, description="File size in bytes")
    mime_type: Optional[str] = Field(None, max_length=100, description="MIME type")
    alt_text: Optional[str] = Field(None, max_length=200, description="Alt text for accessibility")

class MediaCreate(MediaBase):
    product_id: int = Field(..., description="Product ID")


class MediaUpdate(BaseModel):
    type: Optional[str] = Field(None, pattern="^(photo|video)$")
    filename: Optional[str] = Field(None, max_length=255)
    original_filename: Optional[str] = Field(None, max_length=255)
    file_path: Optional[str] = Field(None, max_length=500)
    file_size: Optional[int] = Field(None, ge=0)
    mime_type: Optional[str] = Field(None, max_length=100)
    alt_text: Optional[str] = Field(None, max_length=200)


class MediaResponse(MediaBase):
    id: int
    product_id: int
    created_at: datetime
    sort_order: int

    class Config:
        from_attributes = True
