"""
File upload endpoints
"""
import os
import uuid
from typing import Optional
from pathlib import Path

from fastapi import APIRouter, Depends, File, UploadFile, HTTPException, status
from sqlalchemy.orm import Session

from app.core.dependencies import get_current_active_admin
from app.db.base import get_db
from app.models.admin import AdminUser
from app.models.bull import Bull
from app.core.config import settings

router = APIRouter(prefix="/admin/upload", tags=["Admin - Upload"])

# Define upload directory
UPLOAD_DIR = Path(settings.BASE_DIR) / "uploads" / "bulls"
ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp"}
MAX_FILE_SIZE = 5 * 1024 * 1024  # 5MB


def validate_image_file(file: UploadFile) -> None:
    """Validate uploaded image file"""
    # Check file extension
    file_ext = Path(file.filename).suffix.lower()
    if file_ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid file type. Allowed types: {', '.join(ALLOWED_EXTENSIONS)}"
        )

    # Check content type
    if not file.content_type.startswith("image/"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File must be an image"
        )


@router.post("/bull-photo")
async def upload_bull_photo(
    file: UploadFile = File(...),
    bull_id: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: AdminUser = Depends(get_current_active_admin)
):
    """
    Upload a bull photo

    Args:
        file: Image file (JPG, PNG, WebP)
        bull_id: Optional UUID of bull to update photo for

    Returns:
        File URL and metadata

    Notes:
        - Maximum file size: 5MB
        - Allowed formats: JPG, PNG, WebP
        - If bull_id provided, updates the bull's photo_url
    """
    # Validate file
    validate_image_file(file)

    # Create upload directory if it doesn't exist
    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

    # Generate unique filename
    file_ext = Path(file.filename).suffix.lower()
    unique_filename = f"{uuid.uuid4()}{file_ext}"
    file_path = UPLOAD_DIR / unique_filename

    # Read and validate file size
    contents = await file.read()
    if len(contents) > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File too large. Maximum size: {MAX_FILE_SIZE / (1024 * 1024)}MB"
        )

    # Write file
    try:
        with open(file_path, "wb") as f:
            f.write(contents)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to save file: {str(e)}"
        )

    # Generate URL (relative path for now, will be full URL with CDN in production)
    file_url = f"/uploads/bulls/{unique_filename}"

    # Update bull if bull_id provided
    if bull_id:
        try:
            from uuid import UUID
            bull_uuid = UUID(bull_id)
            bull = db.query(Bull).filter(Bull.id == bull_uuid).first()

            if not bull:
                # Clean up uploaded file
                os.remove(file_path)
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Bull not found"
                )

            # Delete old photo if exists
            if bull.photo_url and bull.photo_url.startswith("/uploads/"):
                old_file_path = Path(settings.BASE_DIR) / bull.photo_url.lstrip("/")
                if old_file_path.exists():
                    try:
                        os.remove(old_file_path)
                    except Exception:
                        pass  # Ignore errors deleting old file

            # Update bull photo
            bull.photo_url = file_url
            db.commit()
            db.refresh(bull)

        except ValueError:
            # Clean up uploaded file
            os.remove(file_path)
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid bull_id format"
            )
        except Exception as e:
            # Clean up uploaded file
            os.remove(file_path)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to update bull: {str(e)}"
            )

    return {
        "filename": unique_filename,
        "url": file_url,
        "size": len(contents),
        "content_type": file.content_type,
        "bull_id": bull_id if bull_id else None,
        "message": "Photo uploaded successfully" + (f" and associated with bull {bull_id}" if bull_id else "")
    }


@router.delete("/bull-photo/{filename}")
async def delete_bull_photo(
    filename: str,
    db: Session = Depends(get_db),
    current_user: AdminUser = Depends(get_current_active_admin)
):
    """
    Delete a bull photo

    Args:
        filename: Name of the file to delete

    Returns:
        Success message
    """
    # Validate filename (prevent directory traversal)
    if "/" in filename or "\\" in filename or ".." in filename:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid filename"
        )

    file_path = UPLOAD_DIR / filename

    if not file_path.exists():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="File not found"
        )

    # Check if file is used by any bull
    file_url = f"/uploads/bulls/{filename}"
    bulls_using_photo = db.query(Bull).filter(Bull.photo_url == file_url).all()

    if bulls_using_photo:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot delete: Photo is used by {len(bulls_using_photo)} bull(s)"
        )

    # Delete file
    try:
        os.remove(file_path)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete file: {str(e)}"
        )

    return {
        "message": "Photo deleted successfully",
        "filename": filename
    }
