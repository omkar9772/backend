"""
Pydantic schemas for Bull
"""
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
from uuid import UUID


class BullBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    owner_id: UUID
    birth_year: Optional[int] = Field(None, ge=1900, le=2100)
    breed: Optional[str] = Field(None, max_length=100)
    color: Optional[str] = Field(None, max_length=50)
    description: Optional[str] = None
    registration_number: Optional[str] = Field(None, max_length=50)


class BullCreate(BaseModel):
    """
    Bull creation schema - linked to owner
    """
    name: str = Field(..., min_length=1, max_length=200)
    owner_id: UUID  # Required - bull is linked to owner
    birth_year: Optional[int] = Field(None, ge=1900, le=2100)
    breed: Optional[str] = Field(None, max_length=100)
    color: Optional[str] = Field(None, max_length=50)
    description: Optional[str] = None
    registration_number: Optional[str] = Field(None, max_length=50)
    photo_url: Optional[str] = Field(None, max_length=500)


class BullUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=200)
    owner_id: Optional[UUID] = None
    birth_year: Optional[int] = Field(None, ge=1900, le=2100)
    breed: Optional[str] = Field(None, max_length=100)
    color: Optional[str] = Field(None, max_length=50)
    description: Optional[str] = None
    photo_url: Optional[str] = Field(None, max_length=500)
    is_active: Optional[bool] = None


class BullResponse(BullBase):
    id: UUID
    photo_url: Optional[str] = None
    is_active: bool
    created_at: datetime
    updated_at: datetime
    owner_name: Optional[str] = None  # Added for frontend display

    class Config:
        from_attributes = True
