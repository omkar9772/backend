"""
Bull management endpoints
"""
from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session

from app.core.dependencies import get_current_active_admin
from app.db.base import get_db
from app.models.admin import AdminUser
from app.models.bull import Bull
from app.models.owner import Owner
from app.schemas.bull import BullCreate, BullUpdate, BullResponse

router = APIRouter(prefix="/admin/bulls", tags=["Admin - Bulls"])


from app.services.storage import storage_service

@router.post("", response_model=BullResponse, status_code=status.HTTP_201_CREATED)
async def create_bull(
    bull: BullCreate,
    db: Session = Depends(get_db),
    current_user: AdminUser = Depends(get_current_active_admin)
):
    """
    Register a new bull - linked to owner
    """
    # Step 1: Fetch owner and validate it exists
    owner = db.query(Owner).filter(Owner.id == bull.owner_id).first()
    if not owner:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Owner with ID '{bull.owner_id}' not found"
        )

    # Step 2: Check if registration number is unique
    if bull.registration_number:
        existing = db.query(Bull).filter(
            Bull.registration_number == bull.registration_number
        ).first()
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Registration number '{bull.registration_number}' already exists"
            )

    # Step 3: Create bull linked to owner
    db_bull = Bull(**bull.model_dump())
    db.add(db_bull)
    db.commit()
    db.refresh(db_bull)
    
    if db_bull.photo_url:
        db_bull.photo_url = storage_service.generate_signed_url(db_bull.photo_url)
        
    return db_bull


@router.get("")
async def list_bulls(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    search: Optional[str] = Query(None),
    owner_id: Optional[UUID] = Query(None),
    is_active: Optional[bool] = Query(None),
    db: Session = Depends(get_db),
    current_user: AdminUser = Depends(get_current_active_admin)
):
    """
    List bulls with pagination and filters
    """
    query = db.query(Bull)

    if search:
        search_filter = f"%{search}%"
        query = query.filter(
            (Bull.name.ilike(search_filter)) |
            (Bull.registration_number.ilike(search_filter))
        )

    if owner_id:
        query = query.filter(Bull.owner_id == owner_id)

    if is_active is not None:
        query = query.filter(Bull.is_active == is_active)

    total = query.count()
    bulls = query.order_by(Bull.name).offset(skip).limit(limit).all()

    # Enrich bulls with owner_name
    result = []
    for bull in bulls:
        # Sign URL
        if bull.photo_url:
            bull.photo_url = storage_service.generate_signed_url(bull.photo_url)
            
        bull_dict = BullResponse.model_validate(bull).model_dump()
        owner = db.query(Owner).filter(Owner.id == bull.owner_id).first()
        bull_dict['owner_name'] = owner.full_name if owner else 'Unknown'
        result.append(bull_dict)

    return {
        "data": result,
        "total": total,
        "skip": skip,
        "limit": limit
    }


@router.get("/{bull_id}", response_model=BullResponse)
async def get_bull(
    bull_id: UUID,
    db: Session = Depends(get_db),
    current_user: AdminUser = Depends(get_current_active_admin)
):
    """Get a bull by ID"""
    bull = db.query(Bull).filter(Bull.id == bull_id).first()
    if not bull:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Bull not found"
        )
        
    if bull.photo_url:
        bull.photo_url = storage_service.generate_signed_url(bull.photo_url)
        
    return bull


@router.put("/{bull_id}", response_model=BullResponse)
async def update_bull(
    bull_id: UUID,
    bull_update: BullUpdate,
    db: Session = Depends(get_db),
    current_user: AdminUser = Depends(get_current_active_admin)
):
    """
    Update a bull
    """
    bull = db.query(Bull).filter(Bull.id == bull_id).first()
    if not bull:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Bull not found"
        )

    # Get update data
    update_data = bull_update.model_dump(exclude_unset=True)

    # If owner_id is being changed, validate new owner exists
    if 'owner_id' in update_data and update_data['owner_id'] != bull.owner_id:
        new_owner = db.query(Owner).filter(Owner.id == update_data['owner_id']).first()
        if not new_owner:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Owner with ID '{update_data['owner_id']}' not found"
            )

    # Apply updates
    for field, value in update_data.items():
        setattr(bull, field, value)

    db.commit()
    db.refresh(bull)
    
    if bull.photo_url:
        bull.photo_url = storage_service.generate_signed_url(bull.photo_url)
        
    return bull


@router.delete("/{bull_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_bull(
    bull_id: UUID,
    db: Session = Depends(get_db),
    current_user: AdminUser = Depends(get_current_active_admin)
):
    """Delete a bull (hard delete)"""
    bull = db.query(Bull).filter(Bull.id == bull_id).first()
    if not bull:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Bull not found"
        )

    # Delete images from storage before deleting bull
    if bull.photo_url:
        storage_service.delete_file(bull.photo_url)
    if bull.thumbnail_url:
        storage_service.delete_file(bull.thumbnail_url)

    db.delete(bull)
    db.commit()
    return None
