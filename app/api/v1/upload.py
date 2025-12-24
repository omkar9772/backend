"""
File upload endpoints
"""
from typing import Optional
from fastapi import APIRouter, Depends, File, UploadFile, HTTPException, status, Form
from sqlalchemy.orm import Session

from app.core.dependencies import get_current_active_admin
from app.db.base import get_db
from app.models.admin import AdminUser
from app.services.storage import storage_service

router = APIRouter(prefix="/admin/upload", tags=["Admin - Upload"])

# Allowed folders for generic upload (images should use specialized endpoints)
ALLOWED_FOLDERS = {"others", "documents"}

# Image folders that require specialized endpoints with thumbnail generation
IMAGE_FOLDERS = {"owners", "race_bulls", "selling_bulls"}

@router.post("")
async def upload_file(
    file: UploadFile = File(...),
    folder: str = Form("others"),
    db: Session = Depends(get_db),
    current_user: AdminUser = Depends(get_current_active_admin)
):
    """
    Generic file upload to GCP (for non-image files)

    For image uploads, use specialized endpoints:
    - Owner images: POST /admin/upload/owner-image
    - Bull images: POST /admin/upload/bull-image

    Args:
        file: File to upload
        folder: Target folder (others, documents)

    Returns:
        url: Blob path (for storage in DB)
        signed_url: Temporary accessible URL (for immediate preview)
    """
    # Block image folders - they must use specialized endpoints
    if folder in IMAGE_FOLDERS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Use POST /admin/upload/{folder.rstrip('s')}-image for {folder} uploads to ensure thumbnails are generated"
        )

    # Validate folder
    if folder not in ALLOWED_FOLDERS:
        folder = "others"

    try:
        # Upload to GCP
        blob_path = await storage_service.upload_file(file, folder=folder)

        # Generate signed URL for immediate use
        signed_url = storage_service.generate_signed_url(blob_path)

        return {
            "url": blob_path, # Store this in DB
            "signed_url": signed_url, # Show this in UI
            "filename": file.filename
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Upload failed: {str(e)}"
        )


@router.post("/bull-image")
async def upload_bull_image(
    file: UploadFile = File(...),
    folder: str = Form("race_bulls"),
    db: Session = Depends(get_db),
    current_user: AdminUser = Depends(get_current_active_admin)
):
    """
    Upload bull image with automatic thumbnail generation
    Optimized for mobile app performance

    Args:
        file: Image file to upload
        folder: Target folder (race_bulls or selling_bulls)

    Returns:
        photo_url: Original image blob path (~100-200 KB)
        thumbnail_url: Thumbnail blob path (~30-50 KB)
        signed_url: Preview URL for original
        thumbnail_signed_url: Preview URL for thumbnail
    """
    # Validate folder for bulls
    if folder not in ["race_bulls", "selling_bulls"]:
        folder = "race_bulls"

    try:
        # Upload with thumbnail generation
        photo_url, thumbnail_url = await storage_service.upload_bull_image(file, folder=folder)

        # Generate signed URLs for preview
        signed_url = storage_service.generate_signed_url(photo_url)
        thumbnail_signed_url = storage_service.generate_signed_url(thumbnail_url)

        return {
            "photo_url": photo_url,  # Store in DB
            "thumbnail_url": thumbnail_url,  # Store in DB
            "signed_url": signed_url,  # Preview original
            "thumbnail_signed_url": thumbnail_signed_url,  # Preview thumbnail
            "filename": file.filename
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Bull image upload failed: {str(e)}"
        )


@router.post("/owner-image")
async def upload_owner_image(
    file: UploadFile = File(...),
    folder: str = Form("owners"),
    db: Session = Depends(get_db),
    current_user: AdminUser = Depends(get_current_active_admin)
):
    """
    Upload owner image with automatic thumbnail generation
    Optimized for mobile app performance

    Args:
        file: Image file to upload
        folder: Target folder (owners)

    Returns:
        photo_url: Original image blob path (~100-200 KB)
        thumbnail_url: Thumbnail blob path (~30-50 KB)
        signed_url: Preview URL for original
        thumbnail_signed_url: Preview URL for thumbnail
    """
    try:
        # Upload with thumbnail generation
        photo_url, thumbnail_url = await storage_service.upload_owner_image(file, folder=folder)

        # Generate signed URLs for preview
        signed_url = storage_service.generate_signed_url(photo_url)
        thumbnail_signed_url = storage_service.generate_signed_url(thumbnail_url)

        return {
            "photo_url": photo_url,  # Store in DB
            "thumbnail_url": thumbnail_url,  # Store in DB
            "signed_url": signed_url,  # Preview original
            "thumbnail_signed_url": thumbnail_signed_url,  # Preview thumbnail
            "filename": file.filename
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Owner image upload failed: {str(e)}"
        )

