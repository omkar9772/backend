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

    - **skip**: Number of records to skip
    - **limit**: Maximum number of records to return
    - **search**: Search by owner name, phone, or email
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

    db.delete(owner)
    db.commit()
    return None
