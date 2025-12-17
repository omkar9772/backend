"""
Marketplace API Endpoints
"""
from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status, File, UploadFile, Form
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field

from app.core.dependencies import get_current_active_admin
from app.db.base import get_db
from app.models.admin import AdminUser
from app.models.marketplace import MarketplaceListing
from app.services.storage import storage_service

router = APIRouter(prefix="/admin/marketplace", tags=["Admin - Marketplace"])

# Requests Schemas
class MarketplaceListingCreate(BaseModel):
    name: str
    owner_name: str
    owner_mobile: str
    location: str
    price: float
    description: Optional[str] = None
    # Image URL is handled via file upload

class MarketplaceListingUpdate(BaseModel):
    name: Optional[str] = None
    owner_name: Optional[str] = None
    owner_mobile: Optional[str] = None
    location: Optional[str] = None
    price: Optional[float] = None
    description: Optional[str] = None
    status: Optional[str] = None
    # Image update handled via separate endpoint or logic if needed

# Response Schema
class MarketplaceListingResponse(BaseModel):
    id: UUID
    name: str
    owner_name: str
    owner_mobile: str
    location: str
    price: float
    image_url: str
    description: Optional[str] = None
    status: str
    
    class Config:
        from_attributes = True

@router.get("", response_model=List[MarketplaceListingResponse])
async def list_marketplace_items(
    skip: int = 0,
    limit: int = 100,
    status_filter: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: AdminUser = Depends(get_current_active_admin)
):
    """List marketplace items"""
    query = db.query(MarketplaceListing)
    
    if status_filter:
        query = query.filter(MarketplaceListing.status == status_filter)
        
    items = query.order_by(MarketplaceListing.created_at.desc()).offset(skip).limit(limit).all()
    
    # Generate signed URLs for all items
    for item in items:
        if item.image_url:
            item.image_url = storage_service.generate_signed_url(item.image_url)
            
    return items

@router.post("", response_model=MarketplaceListingResponse, status_code=status.HTTP_201_CREATED)
async def create_marketplace_item(
    name: str = Form(...),
    owner_name: str = Form(...),
    owner_mobile: str = Form(...),
    location: str = Form(...),
    price: float = Form(...),
    description: Optional[str] = Form(None),
    image: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: AdminUser = Depends(get_current_active_admin)
):
    """Create a new marketplace listing with image upload"""
    
    # 1. Upload image to GCP
    try:
        # Returns blob path (e.g., "selling_bulls/xyz.jpg")
        image_path = await storage_service.upload_file(image, folder="selling_bulls")
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to upload image: {str(e)}"
        )
        
    # 2. Create DB entry
    listing = MarketplaceListing(
        name=name,
        owner_name=owner_name,
        owner_mobile=owner_mobile,
        location=location,
        price=price,
        description=description,
        image_url=image_path, # Store path
        status="available"
    )
    
    db.add(listing)
    db.commit()
    db.refresh(listing)
    
    # 3. Sign URL for response
    if listing.image_url:
        listing.image_url = storage_service.generate_signed_url(listing.image_url)
    
    return listing

@router.put("/{listing_id}", response_model=MarketplaceListingResponse)
async def update_marketplace_item(
    listing_id: UUID,
    name: Optional[str] = Form(None),
    owner_name: Optional[str] = Form(None),
    owner_mobile: Optional[str] = Form(None),
    location: Optional[str] = Form(None),
    price: Optional[float] = Form(None),
    description: Optional[str] = Form(None),
    status: Optional[str] = Form(None),
    image: Optional[UploadFile] = File(None),
    db: Session = Depends(get_db),
    current_user: AdminUser = Depends(get_current_active_admin)
):
    """Update marketplace listing"""
    listing = db.query(MarketplaceListing).filter(MarketplaceListing.id == listing_id).first()
    if not listing:
        raise HTTPException(status_code=404, detail="Listing not found")
        
    # Update fields
    if name: listing.name = name
    if owner_name: listing.owner_name = owner_name
    if owner_mobile: listing.owner_mobile = owner_mobile
    if location: listing.location = location
    if price is not None: listing.price = price
    if description: listing.description = description
    if status: listing.status = status
    
    # Update image if provided
    if image:
        try:
            # Delete old image if it exists
            if listing.image_url:
                storage_service.delete_file(listing.image_url)
                
            # Upload new
            new_path = await storage_service.upload_file(image, folder="selling_bulls")
            listing.image_url = new_path
        except Exception as e:
             raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to upload new image: {str(e)}"
            )

    db.commit()
    db.refresh(listing)
    
    # Sign URL for response
    if listing.image_url:
        listing.image_url = storage_service.generate_signed_url(listing.image_url)
        
    return listing

@router.delete("/{listing_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_marketplace_item(
    listing_id: UUID,
    db: Session = Depends(get_db),
    current_user: AdminUser = Depends(get_current_active_admin)
):
    """Delete marketplace listing"""
    listing = db.query(MarketplaceListing).filter(MarketplaceListing.id == listing_id).first()
    if not listing:
        raise HTTPException(status_code=404, detail="Listing not found")
        
    # Delete image from storage
    if listing.image_url:
        storage_service.delete_file(listing.image_url)
        
    db.delete(listing)
    db.commit()
    return None
