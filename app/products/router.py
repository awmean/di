from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.categories.repository import CategoryRepository
from app.core.database import get_db
from app.products.repository import ProductRepository
from app.products.schemas import ProductResponse, ProductCreate, ProductUpdate

router = APIRouter(prefix="/products", tags=["Products"])


@router.post("/", response_model=ProductResponse, status_code=status.HTTP_201_CREATED)
def create_product(product_data: ProductCreate, db: Session = Depends(get_db)):
    """Create new product"""
    # Check if slug already exists
    existing = ProductRepository.get_by_slug(db, product_data.slug)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Slug already exists"
        )

    # Check if SKU already exists (if provided)
    if product_data.sku:
        existing_sku = ProductRepository.get_by_sku(db, product_data.sku)
        if existing_sku:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="SKU already exists"
            )

    # Validate category exists
    category = CategoryRepository.get_by_id(db, product_data.category_id)
    if not category:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Category not found"
        )

    # Validate parent_id if provided
    if product_data.parent_id:
        parent = ProductRepository.get_by_id(db, product_data.parent_id)
        if not parent:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Parent product not found",
            )

    product_dict = product_data.model_dump()
    product = ProductRepository.create(db=db, **product_dict)
    return product


@router.put("/{product_id}", response_model=ProductResponse)
def update_product(
    product_id: int, product_data: ProductUpdate, db: Session = Depends(get_db)
):
    """Update product"""
    # Check if product exists
    existing_product = ProductRepository.get_by_id(db, product_id)
    if not existing_product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Product not found"
        )

    # Check slug uniqueness if being updated
    if product_data.slug and product_data.slug != existing_product.slug:
        if ProductRepository.get_by_slug(db, product_data.slug):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="Slug already exists"
            )

    # Check SKU uniqueness if being updated
    if product_data.sku and product_data.sku != existing_product.sku:
        if ProductRepository.get_by_sku(db, product_data.sku):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="SKU already exists"
            )

    # Validate category if being updated
    if (
        product_data.category_id
        and product_data.category_id != existing_product.category_id
    ):
        category = CategoryRepository.get_by_id(db, product_data.category_id)
        if not category:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="Category not found"
            )

    # Validate parent_id if being updated
    if product_data.parent_id and product_data.parent_id != existing_product.parent_id:
        if product_data.parent_id == product_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Product cannot be its own parent",
            )

        parent = ProductRepository.get_by_id(db, product_data.parent_id)
        if not parent:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Parent product not found",
            )

    update_data = product_data.model_dump(exclude_unset=True)
    product = ProductRepository.update(db, product_id, **update_data)
    return product


@router.delete("/{product_id}")
def delete_product(product_id: int, db: Session = Depends(get_db)):
    """Delete product"""
    if not ProductRepository.delete(db, product_id):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Product not found"
        )
    return {"message": "Product deleted successfully"}
