# app/api/routers/media.py
from typing import List

from app.core.database import get_db
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.repositories.media_repository import MediaRepository
from app.repositories.product_repository import ProductRepository
from app.schemas.common import MessageResponse
from app.schemas.media import MediaCreate, MediaUpdate, MediaResponse

router = APIRouter(prefix="/media", tags=["Media"])


@router.post("/", response_model=MediaResponse, status_code=status.HTTP_201_CREATED)
def create_media(
        media_data: MediaCreate,
        db: Session = Depends(get_db)
):
    """Create new media"""
    # Validate product exists
    product = ProductRepository.get_by_id(db, media_data.product_id)
    if not product:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Product not found"
        )

    media_dict = media_data.model_dump()
    media = MediaRepository.create(db=db, **media_dict)
    return media


@router.get("/product/{product_id}", response_model=List[MediaResponse])
def get_product_media(
        product_id: int,
        media_type: str = None,
        db: Session = Depends(get_db)
):
    """Get all media for a product"""
    # Validate product exists
    product = ProductRepository.get_by_id(db, product_id)
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found"
        )

    return MediaRepository.get_by_product(db=db, product_id=product_id, type=media_type)


@router.get("/{media_id}", response_model=MediaResponse)
def get_media(
        media_id: int,
        db: Session = Depends(get_db)
):
    """Get media by ID"""
    media = MediaRepository.get_by_id(db, media_id)
    if not media:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Media not found"
        )
    return media


@router.put("/{media_id}", response_model=MediaResponse)
def update_media(
        media_id: int,
        media_data: MediaUpdate,
        db: Session = Depends(get_db)
):
    """Update media"""
    existing_media = MediaRepository.get_by_id(db, media_id)
    if not existing_media:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Media not found"
        )

    update_data = media_data.model_dump(exclude_unset=True)
    media = MediaRepository.update(db, media_id, **update_data)
    return media


@router.put("/{media_id}/set-main", response_model=MessageResponse)
def set_main_media(
        media_id: int,
        db: Session = Depends(get_db)
):
    """Set media as main for its product"""
    media = MediaRepository.get_by_id(db, media_id)
    if not media:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Media not found"
        )

    if media.type != 'photo':
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only photos can be set as main"
        )

    success = MediaRepository.set_main_image(db, media.product_id, media_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to set main image"
        )

    return MessageResponse(message="Main image set successfully")


@router.delete("/{media_id}", response_model=MessageResponse)
def delete_media(
        media_id: int,
        db: Session = Depends(get_db)
):
    """Delete media"""
    if not MediaRepository.delete(db, media_id):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Media not found"
        )
    return MessageResponse(message="Media deleted successfully")
