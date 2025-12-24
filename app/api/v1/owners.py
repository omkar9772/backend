"""
Owner management endpoints
"""
from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session

from app.core.dependencies import get_current_active_admin
from app.db.base import get_db
from app.models.admin import AdminUser
from app.models.owner import Owner
from app.schemas.owner import OwnerCreate, OwnerUpdate, OwnerResponse

router = APIRouter(prefix="/admin/owners", tags=["Admin - Owners"])


from app.services.storage import storage_service

@router.post("", response_model=OwnerResponse, status_code=status.HTTP_201_CREATED)
async def create_owner(
    owner: OwnerCreate,
    db: Session = Depends(get_db),
    current_user: AdminUser = Depends(get_current_active_admin)
):
    """Create a new owner"""
    db_owner = Owner(**owner.model_dump())
    db.add(db_owner)
    db.commit()
    db.refresh(db_owner)
    
    # Sign URL if present (though create likely sends URL string, we might want to ensure it's valid)
    if db_owner.photo_url:
        db_owner.photo_url = storage_service.generate_signed_url(db_owner.photo_url)
        
    return db_owner


@router.get("")
async def list_owners(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    search: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_user: AdminUser = Depends(get_current_active_admin)
):
    """
    List owners with pagination and filters
    """
    query = db.query(Owner)

    if search:
        search_filter = f"%{search}%"
        query = query.filter(
            (Owner.full_name.ilike(search_filter)) |
            (Owner.phone_number.ilike(search_filter)) |
            (Owner.email.ilike(search_filter))
        )

    total = query.count()
    owners = query.order_by(Owner.full_name).offset(skip).limit(limit).all()
    
    # Generate signed URLs
    for owner in owners:
        if owner.photo_url:
            owner.photo_url = storage_service.generate_signed_url(owner.photo_url)

    return {
        "data": owners,
        "total": total,
        "skip": skip,
        "limit": limit
    }


@router.get("/{owner_id}", response_model=OwnerResponse)
async def get_owner(
    owner_id: UUID,
    db: Session = Depends(get_db),
    current_user: AdminUser = Depends(get_current_active_admin)
):
    """Get an owner by ID"""
    owner = db.query(Owner).filter(Owner.id == owner_id).first()
    if not owner:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Owner not found"
        )
        
    if owner.photo_url:
        owner.photo_url = storage_service.generate_signed_url(owner.photo_url)
        
    return owner


@router.put("/{owner_id}", response_model=OwnerResponse)
async def update_owner(
    owner_id: UUID,
    owner_update: OwnerUpdate,
    db: Session = Depends(get_db),
    current_user: AdminUser = Depends(get_current_active_admin)
):
    """Update an owner"""
    owner = db.query(Owner).filter(Owner.id == owner_id).first()
    if not owner:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Owner not found"
        )

    # Update fields
    update_data = owner_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(owner, field, value)

    db.commit()
    db.refresh(owner)
    
    if owner.photo_url:
        owner.photo_url = storage_service.generate_signed_url(owner.photo_url)
        
    return owner


@router.delete("/{owner_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_owner(
    owner_id: UUID,
    db: Session = Depends(get_db),
    current_user: AdminUser = Depends(get_current_active_admin)
):
    """Delete an owner"""
    owner = db.query(Owner).filter(Owner.id == owner_id).first()
    if not owner:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Owner not found"
        )

    # Delete images from storage before deleting owner
    if owner.photo_url:
        storage_service.delete_file(owner.photo_url)
    if owner.thumbnail_url:
        storage_service.delete_file(owner.thumbnail_url)

    db.delete(owner)
    db.commit()
    return None
