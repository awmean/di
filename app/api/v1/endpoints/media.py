import os
import uuid
from pathlib import Path
from typing import List

from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.repositories.media_repository import MediaRepository
from app.repositories.product_repository import ProductRepository
from app.schemas.common import MessageResponse
from app.schemas.media import MediaCreate, MediaUpdate, MediaResponse

router = APIRouter(prefix="/media", tags=["Media"])

# Configuration - you might want to put these in your settings
ALLOWED_IMAGE_TYPES = {"image/jpeg", "image/jpg", "image/png", "image/webp", "image/gif"}
ALLOWED_VIDEO_TYPES = {"video/mp4", "video/avi", "video/mov", "video/wmv", "video/webm"}
MAX_FILE_SIZE = 50 * 1024 * 1024  # 50MB
UPLOAD_DIR = "uploads/media"

# Ensure upload directory exists
os.makedirs(UPLOAD_DIR, exist_ok=True)


def validate_file(file: UploadFile, file_type: str) -> None:
    """Validate uploaded file"""
    if not file.filename:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No file provided"
        )

    # Check file size
    if file.size and file.size > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File size too large. Maximum allowed: {MAX_FILE_SIZE // (1024 * 1024)}MB"
        )

    # Check file type
    allowed_types = ALLOWED_IMAGE_TYPES if file_type == "photo" else ALLOWED_VIDEO_TYPES
    if file.content_type not in allowed_types:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid file type. Allowed types: {', '.join(allowed_types)}"
        )


def generate_filename(original_filename: str) -> str:
    """Generate unique filename"""
    file_extension = Path(original_filename).suffix.lower()
    unique_filename = f"{uuid.uuid4()}{file_extension}"
    return unique_filename


async def save_file(file: UploadFile, filename: str) -> str:
    """Save uploaded file and return file path"""
    file_path = os.path.join(UPLOAD_DIR, filename)

    try:
        with open(file_path, "wb") as buffer:
            content = await file.read()
            buffer.write(content)
        return file_path
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to save file: {str(e)}"
        )


@router.post("/upload", response_model=MediaResponse, status_code=status.HTTP_201_CREATED)
async def upload_media(
        product_id: int = Form(...),
        media_type: str = Form(..., regex="^(photo|video)$"),
        alt_text: str = Form(None),
        sort_order: int = Form(0),
        is_main: bool = Form(False),
        file: UploadFile = File(...),
        db: Session = Depends(get_db)
):
    """Upload media file for a product"""
    # Validate product exists
    product = ProductRepository.get_by_id(db, product_id)
    if not product:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Product not found"
        )

    # Validate file
    validate_file(file, media_type)

    # Generate unique filename
    filename = generate_filename(file.filename)

    # Save file
    file_path = await save_file(file, filename)

    try:
        # Create media record
        media = MediaRepository.create(
            db=db,
            product_id=product_id,
            type=media_type,
            filename=filename,
            original_filename=file.filename,
            file_path=file_path,
            file_size=file.size,
            mime_type=file.content_type,
            alt_text=alt_text,
            sort_order=sort_order,
            is_main=is_main
        )

        # If this is set as main image, update other images
        if is_main and media_type == "photo":
            MediaRepository.set_main_image(db, product_id, media.id)

        return media

    except Exception as e:
        # Clean up file if database operation fails
        if os.path.exists(file_path):
            os.remove(file_path)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create media record: {str(e)}"
        )


@router.post("/upload/multiple", response_model=List[MediaResponse], status_code=status.HTTP_201_CREATED)
async def upload_multiple_media(
        product_id: int = Form(...),
        media_type: str = Form(..., regex="^(photo|video)$"),
        files: List[UploadFile] = File(...),
        db: Session = Depends(get_db)
):
    """Upload multiple media files for a product"""
    # Validate product exists
    product = ProductRepository.get_by_id(db, product_id)
    if not product:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Product not found"
        )

    if len(files) > 10:  # Limit number of files
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Maximum 10 files allowed per upload"
        )

    created_media = []
    created_files = []  # Track created files for cleanup on error

    try:
        for i, file in enumerate(files):
            # Validate file
            validate_file(file, media_type)

            # Generate unique filename
            filename = generate_filename(file.filename)

            # Save file
            file_path = await save_file(file, filename)
            created_files.append(file_path)

            # Create media record
            media = MediaRepository.create(
                db=db,
                product_id=product_id,
                type=media_type,
                filename=filename,
                original_filename=file.filename,
                file_path=file_path,
                file_size=file.size,
                mime_type=file.content_type,
                sort_order=i,  # Auto-increment sort order
                is_main=False  # Don't auto-set main for batch uploads
            )
            created_media.append(media)

        return created_media

    except Exception as e:
        # Clean up all created files on error
        for file_path in created_files:
            if os.path.exists(file_path):
                os.remove(file_path)

        # Clean up any created database records
        for media in created_media:
            try:
                MediaRepository.delete(db, media.id)
            except:
                pass

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to upload files: {str(e)}"
        )
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


@router.put("/{media_id}/set-order", response_model=MediaResponse)
def update_media_sort_order(
        media_id: int,
        sort_order: int,
        db: Session = Depends(get_db)
):
    """Update media sort order"""
    existing_media = MediaRepository.get_by_id(db, media_id)
    if not existing_media:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Media not found"
        )
    media = MediaRepository.update(db, media_id, sort_order=sort_order)
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
