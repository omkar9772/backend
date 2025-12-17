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

# Allowed folders map to prevent arbitrary folder creation
ALLOWED_FOLDERS = {"owners", "race_bulls", "selling_bulls", "others"}

@router.post("")
async def upload_file(
    file: UploadFile = File(...),
    folder: str = Form("others"),
    db: Session = Depends(get_db),
    current_user: AdminUser = Depends(get_current_active_admin)
):
    """
    Generic file upload to GCP
    
    Args:
        file: File to upload
        folder: Target folder (owners, race_bulls, selling_bulls)
        
    Returns:
        url: Blob path (for storage in DB)
        signed_url: Temporary accessible URL (for immediate preview)
    """
    # Validate folder
    if folder not in ALLOWED_FOLDERS:
        # Fallback or error? Let's strict for now or default to others
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

