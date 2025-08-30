import os
import uuid
from pathlib import Path
from typing import List, Optional, Dict, Tuple

from PIL import Image
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.media.models import Media
from app.media.repository import MediaRepository
from app.media.schemas import MediaResponse
from app.products.repository import ProductRepository

router = APIRouter(prefix="/media", tags=["Media"])

# Configuration
ALLOWED_IMAGE_TYPES = {
    "image/jpeg",
    "image/jpg",
    "image/png",
    "image/webp",
    "image/gif",
}
ALLOWED_VIDEO_TYPES = {"video/mp4", "video/avi", "video/mov", "video/wmv", "video/webm"}

ALLOWED_TYPES = ALLOWED_IMAGE_TYPES | ALLOWED_VIDEO_TYPES
MAX_FILE_SIZE = 100 * 1024 * 1024  # 100MB
UPLOAD_DIR = "uploads/media"

# Размеры для изображений товаров
IMAGE_SIZES = {
    'thumb': (300, 300),  # миниатюра для каталога
    'medium': (800, 800),  # основное изображение
    'large': (1200, 1200),  # детальный просмотр
    'original': None  # оригинал (без изменений)
}

# Ensure upload directory exists
os.makedirs(UPLOAD_DIR, exist_ok=True)


def validate_file(file: UploadFile) -> Optional[str]:
    """Validate uploaded file"""
    if not file.filename:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="No file provided"
        )

    if file.size and file.size > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File size too large. Maximum allowed: {MAX_FILE_SIZE // (1024 * 1024)}MB",
        )

    if file.content_type not in ALLOWED_TYPES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid file type. Allowed types: {', '.join(ALLOWED_TYPES)}",
        )

    return 'photo' if file.content_type in ALLOWED_IMAGE_TYPES else 'video' if file.content_type in ALLOWED_VIDEO_TYPES else None


def generate_filename(original_filename: str) -> Tuple[str, str]:
    """Generate unique filename base and extension"""
    file_extension = Path(original_filename).suffix.lower()
    unique_name = str(uuid.uuid4())
    return unique_name, file_extension


def resize_image(image_path: str, size: Tuple[int, int], quality: int = 85) -> Image.Image:
    """Resize image maintaining aspect ratio"""
    with Image.open(image_path) as img:
        # Convert RGBA to RGB if necessary for JPEG
        if img.mode == 'RGBA':
            img = img.convert('RGB')

        # Calculate new size maintaining aspect ratio
        img.thumbnail(size, Image.Resampling.LANCZOS)
        return img.copy()  # Return a copy to avoid closed file issues


def create_image_variants(original_path: str, base_filename: str, file_extension: str) -> Dict[str, str]:
    """Create different sized variants of an image"""
    variants = {}

    try:
        # Сохраняем оригинал с правильным именем
        original_filename = f"{base_filename}_original{file_extension}"
        original_full_path = os.path.join(UPLOAD_DIR, original_filename)

        # Копируем оригинал
        with open(original_path, 'rb') as src:
            with open(original_full_path, 'wb') as dst:
                dst.write(src.read())
        variants['original'] = original_filename

        # Создаем варианты разных размеров
        for size_name, dimensions in IMAGE_SIZES.items():
            if size_name == 'original':
                continue

            variant_filename = f"{base_filename}_{size_name}{file_extension}"
            variant_path = os.path.join(UPLOAD_DIR, variant_filename)

            # Изменяем размер и сохраняем
            resized_img = resize_image(original_path, dimensions)

            # Определяем формат для сохранения
            if file_extension.lower() in ['.jpg', '.jpeg']:
                resized_img.save(variant_path, format='JPEG', quality=85, optimize=True)
            elif file_extension.lower() == '.png':
                resized_img.save(variant_path, format='PNG', optimize=True)
            elif file_extension.lower() == '.webp':
                resized_img.save(variant_path, format='WEBP', quality=85, optimize=True)
            else:
                # Для других форматов сохраняем как JPEG
                resized_img.save(variant_path, format='JPEG', quality=85, optimize=True)

            variants[size_name] = variant_filename

        return variants

    except Exception as e:
        # Очищаем созданные файлы при ошибке
        for variant_file in variants.values():
            variant_path = os.path.join(UPLOAD_DIR, variant_file)
            if os.path.exists(variant_path):
                os.remove(variant_path)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create image variants: {str(e)}"
        )


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
            detail=f"Failed to save file: {str(e)}",
        )


@router.post(
    "/upload", response_model=MediaResponse, status_code=status.HTTP_201_CREATED
)
async def upload_media(
        product_id: int = Form(...),
        alt_text: str = Form(None),
        file: UploadFile = File(...),
        db: Session = Depends(get_db),
):
    """Upload media file for a product"""
    # Validate product exists
    product = ProductRepository.get_by_id(db, product_id)
    if not product:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Product not found"
        )

    # Validate file
    media_type = validate_file(file)

    # Generate unique filename
    base_filename, file_extension = generate_filename(file.filename)
    temp_filename = f"{base_filename}_temp{file_extension}"

    # Save temporary file
    temp_file_path = await save_file(file, temp_filename)

    try:
        filename_variants = None

        if media_type == 'photo':
            # Создаем варианты размеров для изображений
            variants = create_image_variants(temp_file_path, base_filename, file_extension)
            filename = variants['medium']  # Основной файл - средний размер
            file_path = os.path.join(UPLOAD_DIR, filename)
            filename_variants = variants

            # Удаляем временный файл
            if os.path.exists(temp_file_path):
                os.remove(temp_file_path)
        else:
            # Для видео просто переименовываем
            filename = f"{base_filename}{file_extension}"
            file_path = os.path.join(UPLOAD_DIR, filename)
            os.rename(temp_file_path, file_path)

        # Create media record с вариантами размеров
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
            filename_variants=filename_variants,
        )

        return media

    except Exception as e:
        # Clean up files if database operation fails
        if os.path.exists(temp_file_path):
            os.remove(temp_file_path)
        if 'variants' in locals():
            for variant_file in variants.values():
                variant_path = os.path.join(UPLOAD_DIR, variant_file)
                if os.path.exists(variant_path):
                    os.remove(variant_path)
        elif 'file_path' in locals() and os.path.exists(file_path):
            os.remove(file_path)

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create media record: {str(e)}",
        )


@router.post(
    "/upload/multiple",
    response_model=List[MediaResponse],
    status_code=status.HTTP_201_CREATED,
)
async def upload_multiple_media(
        product_id: int = Form(...),
        files: List[UploadFile] = File(...),
        db: Session = Depends(get_db),
):
    """Upload multiple media files for a product"""
    # Validate product exists
    product = ProductRepository.get_by_id(db, product_id)
    if not product:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Product not found"
        )

    if len(files) > 10:  # Limit number of files
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Maximum 10 files allowed per upload",
        )

    created_media = []
    created_files = []  # Track created files for cleanup on error

    try:
        for i, file in enumerate(files):
            # Validate file
            media_type = validate_file(file)

            # Generate unique filename
            base_filename, file_extension = generate_filename(file.filename)
            temp_filename = f"{base_filename}_temp{file_extension}"

            # Save temporary file
            temp_file_path = await save_file(file, temp_filename)
            created_files.append(temp_file_path)

            filename_variants = None

            if media_type == 'photo':
                # Создаем варианты размеров для изображений
                variants = create_image_variants(temp_file_path, base_filename, file_extension)
                filename = variants['medium']
                file_path = os.path.join(UPLOAD_DIR, filename)
                filename_variants = variants

                # Добавляем все варианты в список для очистки
                for variant_file in variants.values():
                    created_files.append(os.path.join(UPLOAD_DIR, variant_file))

                # Удаляем временный файл
                if os.path.exists(temp_file_path):
                    os.remove(temp_file_path)
                    created_files.remove(temp_file_path)  # Убираем из списка для очистки
            else:
                filename = f"{base_filename}{file_extension}"
                file_path = os.path.join(UPLOAD_DIR, filename)
                os.rename(temp_file_path, file_path)
                # Обновляем путь в списке для очистки
                created_files[created_files.index(temp_file_path)] = file_path

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
                filename_variants=filename_variants,
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
            detail=f"Failed to upload files: {str(e)}",
        )


# Остальные эндпоинты остаются без изменений
@router.patch("/{media_id}/move-up", response_model=MediaResponse)
def move_order_up(media_id: int, db: Session = Depends(get_db)):
    """Update media sort order"""
    existing_media = MediaRepository.get_by_id(db, media_id)
    if not existing_media:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Media not found"
        )

    previous_media = (
        db.query(Media)
        .filter(
            Media.product_id == existing_media.product_id,
            Media.sort_order < existing_media.sort_order,
        )
        .order_by(Media.sort_order.desc())
        .first()
    )

    if not previous_media:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Media is already at the top position",
        )

    current_sort_order = existing_media.sort_order
    previous_sort_order = previous_media.sort_order

    existing_media.sort_order = previous_sort_order
    previous_media.sort_order = current_sort_order

    db.commit()
    db.refresh(existing_media)
    return existing_media


@router.patch("/{media_id}/move-down", response_model=MediaResponse)
def move_order_down(media_id: int, db: Session = Depends(get_db)):
    """Move media sort order down (increase sort_order value)"""
    existing_media = MediaRepository.get_by_id(db, media_id)
    if not existing_media:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Media not found"
        )

    next_media = (
        db.query(Media)
        .filter(
            Media.product_id == existing_media.product_id,
            Media.sort_order > existing_media.sort_order,
        )
        .order_by(Media.sort_order.asc())
        .first()
    )

    if not next_media:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Media is already at the bottom position",
        )

    current_sort_order = existing_media.sort_order
    next_sort_order = next_media.sort_order

    existing_media.sort_order = next_sort_order
    next_media.sort_order = current_sort_order

    db.commit()
    db.refresh(existing_media)
    return existing_media


@router.delete("/{media_id}")
def delete_media(media_id: int, db: Session = Depends(get_db)):
    """Delete media and all its variants"""
    media = MediaRepository.get_by_id(db, media_id)
    if not media:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Media not found"
        )

    # Удаляем все варианты изображения, если это фото
    if media.type == 'photo':
        # Удаляем все варианты по именам полей
        variant_filenames = [
            media.filename_thumb,
            media.filename_medium,
            media.filename_large,
            media.filename_original
        ]

        for variant_filename in variant_filenames:
            if variant_filename:
                variant_path = os.path.join(UPLOAD_DIR, variant_filename)
                if os.path.exists(variant_path):
                    os.remove(variant_path)
    else:
        # Для видео удаляем основной файл
        if os.path.exists(media.file_path):
            os.remove(media.file_path)

    if not MediaRepository.delete(db, media_id):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Media not found"
        )
    return {"message": "Media deleted successfully"}
