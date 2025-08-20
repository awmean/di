# app/api/routers/products.py
from typing import List

from app.core.database import get_db
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.repositories.category_repository import CategoryRepository
from app.repositories.product_repository import ProductRepository
from app.schemas.common import PaginatedResponse, MessageResponse
from app.schemas.filters import ProductFilters
from app.schemas.product import (
    ProductCreate, ProductUpdate, ProductResponse,
    ProductDetailResponse, ProductListResponse, ProductSetResponse
)

router = APIRouter(prefix="/products", tags=["Products"])


@router.post("/", response_model=ProductResponse, status_code=status.HTTP_201_CREATED)
def create_product(
        product_data: ProductCreate,
        db: Session = Depends(get_db)
):
    """Create new product"""
    # Check if slug already exists
    existing = ProductRepository.get_by_slug(db, product_data.slug)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Slug already exists"
        )

    # Check if SKU already exists (if provided)
    if product_data.sku:
        existing_sku = ProductRepository.get_by_sku(db, product_data.sku)
        if existing_sku:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="SKU already exists"
            )

    # Validate category exists
    category = CategoryRepository.get_by_id(db, product_data.category_id)
    if not category:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Category not found"
        )

    # Validate parent_id if provided
    if product_data.parent_id:
        parent = ProductRepository.get_by_id(db, product_data.parent_id)
        if not parent:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Parent product not found"
            )

    product_dict = product_data.model_dump()
    product = ProductRepository.create(db=db, **product_dict)
    return product


@router.get("/", response_model=PaginatedResponse[ProductListResponse])
def get_products(
        skip: int = 0,
        limit: int = 100,
        filters: ProductFilters = Depends(),
        db: Session = Depends(get_db)
):
    """Get all products with filters"""
    products = ProductRepository.get_all(
        db=db,
        skip=skip,
        limit=limit,
        active_only=filters.is_active if filters.is_active is not None else False,
        category_id=filters.category_id,
        featured_only=filters.is_featured if filters.is_featured else False,
        search=filters.search,
        min_price=float(filters.min_price) if filters.min_price else None,
        max_price=float(filters.max_price) if filters.max_price else None,
        sort_by=filters.sort_by,
        sort_order=filters.sort_order
    )

    total = ProductRepository.count(
        db=db,
        active_only=filters.is_active if filters.is_active is not None else False,
        category_id=filters.category_id
    )

    return PaginatedResponse(
        items=products,
        total=total,
        page=(skip // limit) + 1,
        size=limit,
        pages=((total - 1) // limit) + 1 if total > 0 else 0,
        has_next=(skip + limit) < total,
        has_prev=skip > 0
    )


@router.get("/featured", response_model=List[ProductListResponse])
def get_featured_products(
        limit: int = 10,
        db: Session = Depends(get_db)
):
    """Get featured products"""
    return ProductRepository.get_featured(db=db, limit=limit)


@router.get("/{product_id}", response_model=ProductDetailResponse)
def get_product(
        product_id: int,
        db: Session = Depends(get_db)
):
    """Get product by ID with full details"""
    product = ProductRepository.get_by_id(db, product_id)
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found"
        )
    return product


@router.get("/slug/{slug}", response_model=ProductDetailResponse)
def get_product_by_slug(
        slug: str,
        db: Session = Depends(get_db)
):
    """Get product by slug with full details"""
    product = ProductRepository.get_by_slug(db, slug)
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found"
        )
    return product


@router.get("/{product_id}/set", response_model=ProductSetResponse)
def get_product_set(
        product_id: int,
        db: Session = Depends(get_db)
):
    """Get product set with all pieces"""
    product = ProductRepository.get_by_id(db, product_id)
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found"
        )

    if not product.is_set:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Product is not a set"
        )

    return product


@router.put("/{product_id}", response_model=ProductResponse)
def update_product(
        product_id: int,
        product_data: ProductUpdate,
        db: Session = Depends(get_db)
):
    """Update product"""
    # Check if product exists
    existing_product = ProductRepository.get_by_id(db, product_id)
    if not existing_product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found"
        )

    # Check slug uniqueness if being updated
    if product_data.slug and product_data.slug != existing_product.slug:
        if ProductRepository.get_by_slug(db, product_data.slug):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Slug already exists"
            )

    # Check SKU uniqueness if being updated
    if product_data.sku and product_data.sku != existing_product.sku:
        if ProductRepository.get_by_sku(db, product_data.sku):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="SKU already exists"
            )

    # Validate category if being updated
    if product_data.category_id and product_data.category_id != existing_product.category_id:
        category = CategoryRepository.get_by_id(db, product_data.category_id)
        if not category:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Category not found"
            )

    # Validate parent_id if being updated
    if product_data.parent_id and product_data.parent_id != existing_product.parent_id:
        if product_data.parent_id == product_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Product cannot be its own parent"
            )

        parent = ProductRepository.get_by_id(db, product_data.parent_id)
        if not parent:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Parent product not found"
            )

    update_data = product_data.model_dump(exclude_unset=True)
    product = ProductRepository.update(db, product_id, **update_data)
    return product


@router.delete("/{product_id}", response_model=MessageResponse)
def delete_product(
        product_id: int,
        db: Session = Depends(get_db)
):
    """Delete product"""
    if not ProductRepository.delete(db, product_id):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found"
        )
    return MessageResponse(message="Product deleted successfully")
