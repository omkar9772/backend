"""
User Bulls for Sale API Endpoints
Allows authenticated users to list their bulls for sale with restrictions
"""
from typing import List, Optional
from uuid import UUID
from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, status, File, UploadFile, Form
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.api.v1.auth import get_current_app_user
from app.db.base import get_db
from app.models.user import User
from app.models.user_bull import UserBullSell
from app.schemas.user_bull import UserBullSellResponse, UserBullSellListResponse
from app.services.storage import storage_service

router = APIRouter(prefix="/user/bulls", tags=["User Bulls"])

# Constants
MAX_BULLS_PER_USER = 5
MAX_IMAGE_SIZE_MB = 5
ALLOWED_IMAGE_TYPES = {'image/jpeg', 'image/jpg', 'image/png'}
ALLOWED_EXTENSIONS = {'.jpg', '.jpeg', '.png'}


def validate_image(file: UploadFile) -> None:
    """
    Validate image file format and size

    Raises HTTPException if validation fails
    """
    # Check file extension
    if not file.filename:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Filename is required"
        )

    file_ext = file.filename.lower().split('.')[-1]
    if f'.{file_ext}' not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Only JPG and PNG images are allowed. Got: {file_ext}"
        )

    # Check content type
    if file.content_type not in ALLOWED_IMAGE_TYPES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid image format. Only JPG and PNG are allowed. Got: {file.content_type}"
        )

    # Check file size
    file.file.seek(0, 2)  # Seek to end
    file_size = file.file.tell()  # Get position (size)
    file.file.seek(0)  # Reset to beginning

    max_size_bytes = MAX_IMAGE_SIZE_MB * 1024 * 1024
    if file_size > max_size_bytes:
        size_mb = file_size / (1024 * 1024)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Image size must be less than {MAX_IMAGE_SIZE_MB}MB. Got: {size_mb:.2f}MB"
        )


@router.get("", response_model=UserBullSellListResponse)
async def list_my_bulls(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_app_user)
):
    """
    List all bulls listed by the current user

    OPTIMIZED:
    - Removed separate count() query - calculate from fetched data
    - Use thumbnails for list view (smaller/faster)
    - 7-day signed URL expiration for better caching
    """
    bulls = db.query(UserBullSell).filter(
        UserBullSell.user_id == current_user.id
    ).order_by(UserBullSell.created_at.desc()).all()

    # OPTIMIZED: Calculate active count from already fetched bulls (no extra query)
    active_count = sum(1 for bull in bulls if bull.status == 'available')

    # Generate signed URLs with thumbnails for list view
    for bull in bulls:
        if bull.image_url:
            # Use THUMBNAIL for list view (smaller/faster)
            thumbnail_path = bull.thumbnail_url or bull.image_url
            bull.image_url = storage_service.generate_signed_url(thumbnail_path, expiration=604800)  # 7 days

    return UserBullSellListResponse(
        bulls=bulls,
        total=len(bulls),
        active_count=active_count,
        max_allowed=MAX_BULLS_PER_USER
    )


@router.get("/{bull_id}", response_model=UserBullSellResponse)
async def get_bull_detail(
    bull_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_app_user)
):
    """Get details of a specific bull (must be owned by current user)"""
    bull = db.query(UserBullSell).filter(
        UserBullSell.id == bull_id,
        UserBullSell.user_id == current_user.id
    ).first()

    if not bull:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Bull not found or you don't have permission to view it"
        )

    # For detail view, serve ORIGINAL high-quality image
    if bull.image_url:
        bull.image_url = storage_service.generate_signed_url(bull.image_url, expiration=604800)  # 7 days

    return bull


@router.post("", response_model=UserBullSellResponse, status_code=status.HTTP_201_CREATED)
async def create_bull_listing(
    name: str = Form(...),
    price: float = Form(...),
    image: UploadFile = File(...),
    owner_name: str = Form(...),
    owner_mobile: str = Form(...),
    breed: Optional[str] = Form(None),
    birth_year: Optional[int] = Form(None),
    color: Optional[str] = Form(None),
    description: Optional[str] = Form(None),
    location: Optional[str] = Form(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_app_user)
):
    """
    Create a new bull listing

    Restrictions:
    - Maximum 5 active bulls per user
    - Only JPG/PNG images allowed
    - Image size must be less than 5MB
    - Bull listing expires after 30 days
    """

    # 1. Check if user has reached the limit of active bulls
    active_count = db.query(func.count(UserBullSell.id)).filter(
        UserBullSell.user_id == current_user.id,
        UserBullSell.status == 'available'
    ).scalar()

    if active_count >= MAX_BULLS_PER_USER:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"You can only have {MAX_BULLS_PER_USER} active bull listings. Please delete or wait for an existing listing to expire."
        )

    # 2. Validate image
    validate_image(image)

    # 3. Validate price
    if price <= 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Price must be greater than 0"
        )

    # 4. Upload image to GCP with automatic thumbnail generation
    try:
        image_path, thumbnail_path = await storage_service.upload_bull_image(image, folder="user_bulls_sell")
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to upload image: {str(e)}"
        )

    # 5. Create bull listing
    bull = UserBullSell(
        user_id=current_user.id,
        name=name,
        breed=breed,
        birth_year=birth_year,
        color=color,
        description=description,
        price=price,
        image_url=image_path,
        thumbnail_url=thumbnail_path,
        location=location,
        owner_name=owner_name,
        owner_mobile=owner_mobile,
        status="available",
        expires_at=datetime.utcnow() + timedelta(days=30)
    )

    db.add(bull)
    db.commit()
    db.refresh(bull)

    # 6. Generate signed URL for response (use original for detail/create response)
    if bull.image_url:
        bull.image_url = storage_service.generate_signed_url(bull.image_url, expiration=604800)  # 7 days

    return bull


@router.put("/{bull_id}", response_model=UserBullSellResponse)
async def update_bull_listing(
    bull_id: UUID,
    name: Optional[str] = Form(None),
    price: Optional[float] = Form(None),
    breed: Optional[str] = Form(None),
    birth_year: Optional[int] = Form(None),
    color: Optional[str] = Form(None),
    description: Optional[str] = Form(None),
    location: Optional[str] = Form(None),
    owner_name: Optional[str] = Form(None),
    owner_mobile: Optional[str] = Form(None),
    status: Optional[str] = Form(None),
    image: Optional[UploadFile] = File(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_app_user)
):
    """Update a bull listing (must be owned by current user)"""

    # 1. Get bull and verify ownership
    bull = db.query(UserBullSell).filter(
        UserBullSell.id == bull_id,
        UserBullSell.user_id == current_user.id
    ).first()

    if not bull:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Bull not found or you don't have permission to update it"
        )

    # 2. Update fields
    if name is not None:
        bull.name = name
    if price is not None:
        if price <= 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Price must be greater than 0"
            )
        bull.price = price
    if breed is not None:
        bull.breed = breed
    if birth_year is not None:
        bull.birth_year = birth_year
    if color is not None:
        bull.color = color
    if description is not None:
        bull.description = description
    if location is not None:
        bull.location = location
    if owner_name is not None:
        bull.owner_name = owner_name
    if owner_mobile is not None:
        bull.owner_mobile = owner_mobile
    if status is not None:
        if status not in ['available', 'sold', 'expired']:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Status must be one of: available, sold, expired"
            )
        bull.status = status

    # 3. Update image if provided
    if image:
        validate_image(image)
        try:
            # Delete old images (both original and thumbnail)
            if bull.image_url:
                storage_service.delete_file(bull.image_url)
            if bull.thumbnail_url:
                storage_service.delete_file(bull.thumbnail_url)

            # Upload new image with automatic thumbnail generation
            new_image_path, new_thumbnail_path = await storage_service.upload_bull_image(image, folder="user_bulls_sell")
            bull.image_url = new_image_path
            bull.thumbnail_url = new_thumbnail_path
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to upload new image: {str(e)}"
            )

    bull.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(bull)

    # 4. Generate signed URL for response (use original for detail/update response)
    if bull.image_url:
        bull.image_url = storage_service.generate_signed_url(bull.image_url, expiration=604800)  # 7 days

    return bull


@router.delete("/{bull_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_bull_listing(
    bull_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_app_user)
):
    """Delete a bull listing (must be owned by current user)"""

    bull = db.query(UserBullSell).filter(
        UserBullSell.id == bull_id,
        UserBullSell.user_id == current_user.id
    ).first()

    if not bull:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Bull not found or you don't have permission to delete it"
        )

    # Delete images from storage (both original and thumbnail)
    if bull.image_url:
        storage_service.delete_file(bull.image_url)
    if bull.thumbnail_url:
        storage_service.delete_file(bull.thumbnail_url)

    db.delete(bull)
    db.commit()

    return None
