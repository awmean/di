
# app/api/routers/categories.py
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.repositories.category_repository import CategoryRepository
from app.schemas.category import CategoryCreate, CategoryUpdate, CategoryResponse
from app.schemas.common import PaginatedResponse, MessageResponse
from app.schemas.filters import CategoryFilters

router = APIRouter(prefix="/categories", tags=["Categories"])


@router.post("/", response_model=CategoryResponse, status_code=status.HTTP_201_CREATED)
def create_category(
        category_data: CategoryCreate,
        db: Session = Depends(get_db)
):
    """Create new category"""
    # Check if slug already exists
    existing = CategoryRepository.get_by_slug(db, category_data.slug)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Slug already exists"
        )

    # Validate parent_id if provided
    if category_data.parent_id:
        parent = CategoryRepository.get_by_id(db, category_data.parent_id)
        if not parent:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Parent category not found"
            )

    category = CategoryRepository.create(
        db=db,
        name=category_data.name,
        slug=category_data.slug,
        description=category_data.description,
        parent_id=category_data.parent_id,
        sort_order=category_data.sort_order,
        is_active=category_data.is_active
    )
    return category


@router.get("/", response_model=PaginatedResponse[CategoryResponse])
def get_categories(
        skip: int = 0,
        limit: int = 100,
        filters: CategoryFilters = Depends(),
        db: Session = Depends(get_db)
):
    """Get all categories with filters"""
    categories = CategoryRepository.get_all(
        db=db,
        skip=skip,
        limit=limit,
        active_only=filters.is_active if filters.is_active is not None else False,
        parent_id=filters.parent_id
    )

    total = CategoryRepository.count(
        db=db,
        active_only=filters.is_active if filters.is_active is not None else False
    )

    return PaginatedResponse(
        items=categories,
        total=total,
        page=(skip // limit) + 1,
        size=limit,
        pages=((total - 1) // limit) + 1 if total > 0 else 0,
        has_next=(skip + limit) < total,
        has_prev=skip > 0
    )


@router.get("/root", response_model=List[CategoryResponse])
def get_root_categories(
        active_only: bool = Query(False, description="Filter only active categories"),
        db: Session = Depends(get_db)
):
    """Get root categories (categories without parent)"""
    return CategoryRepository.get_root_categories(db=db, active_only=active_only)


@router.get("/{category_id}", response_model=CategoryResponse)
def get_category(
        category_id: int,
        db: Session = Depends(get_db)
):
    """Get category by ID"""
    category = CategoryRepository.get_by_id(db, category_id)
    if not category:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Category not found"
        )
    return category


@router.get("/slug/{slug}", response_model=CategoryResponse)
def get_category_by_slug(
        slug: str,
        db: Session = Depends(get_db)
):
    """Get category by slug"""
    category = CategoryRepository.get_by_slug(db, slug)
    if not category:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Category not found"
        )
    return category


@router.put("/{category_id}", response_model=CategoryResponse)
def update_category(
        category_id: int,
        category_data: CategoryUpdate,
        db: Session = Depends(get_db)
):
    """Update category"""
    # Check if category exists
    existing_category = CategoryRepository.get_by_id(db, category_id)
    if not existing_category:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Category not found"
        )

    # Check slug uniqueness if being updated
    if category_data.slug and category_data.slug != existing_category.slug:
        if CategoryRepository.get_by_slug(db, category_data.slug):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Slug already exists"
            )

    # Validate parent_id if being updated
    if category_data.parent_id and category_data.parent_id != existing_category.parent_id:
        if category_data.parent_id == category_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Category cannot be its own parent"
            )

        parent = CategoryRepository.get_by_id(db, category_data.parent_id)
        if not parent:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Parent category not found"
            )

    update_data = category_data.model_dump(exclude_unset=True)
    category = CategoryRepository.update(db, category_id, **update_data)
    return category


@router.delete("/{category_id}", response_model=MessageResponse)
def delete_category(
        category_id: int,
        db: Session = Depends(get_db)
):
    """Delete category"""
    if not CategoryRepository.delete(db, category_id):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Category not found"
        )
    return MessageResponse(message="Category deleted successfully")

