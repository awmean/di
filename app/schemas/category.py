import re
from datetime import datetime
from typing import Optional, List

from pydantic import BaseModel, Field, field_validator


class CategoryMediaBase(BaseModel):
    type: str = Field(..., pattern="^(photo|video|icon)$", description="Media type")
    filename: str = Field(..., max_length=255)
    original_filename: Optional[str] = Field(None, max_length=255)
    file_path: str = Field(..., max_length=500)
    file_size: Optional[int] = Field(None, ge=0)
    mime_type: Optional[str] = Field(None, max_length=100)
    alt_text: Optional[str] = Field(None, max_length=200)
    sort_order: int = Field(default=0)
    is_main: bool = Field(default=False)

class CategoryMediaCreate(CategoryMediaBase):
    category_id: int


class CategoryMediaResponse(CategoryMediaBase):
    id: int
    category_id: int
    created_at: datetime

    class Config:
        from_attributes = True

class CategoryBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=100, description="Category name")
    slug: str = Field(..., max_length=100, description="URL slug")
    description: Optional[str] = Field(None, description="Category description")
    parent_id: Optional[int] = Field(None, description="Parent category ID")
    sort_order: int = Field(default=0, description="Sort order")
    is_active: bool = Field(default=True, description="Whether category is active")

    @field_validator('slug')
    def validate_slug(cls, v):
        if not re.match(r'^[a-z0-9-]+$', v):
            raise ValueError('Slug can only contain lowercase letters, numbers, and hyphens')
        return v

class CategoryCreate(CategoryBase):
    pass


class CategoryUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    slug: Optional[str] = Field(None, max_length=100)
    description: Optional[str] = None
    parent_id: Optional[int] = None
    sort_order: Optional[int] = None
    is_active: Optional[bool] = None

    @field_validator('slug')
    def validate_slug(cls, v):
        if v is not None and not re.match(r'^[a-z0-9-]+$', v):
            raise ValueError('Slug can only contain lowercase letters, numbers, and hyphens')
        return v


class CategoryResponse(CategoryBase):
    id: int
    created_at: datetime
    updated_at: datetime
    media: List[CategoryMediaResponse] = []
    children: List['CategoryResponse'] = []
    parent_id: Optional[int] = None

    class Config:
        from_attributes = True


# Enable forward references
CategoryResponse.model_rebuild()
