"""
User Bull Sell Schemas
"""
from typing import Optional
from uuid import UUID
from datetime import datetime
from pydantic import BaseModel, Field, field_validator


class UserBullSellCreate(BaseModel):
    """Schema for creating a user bull listing"""
    name: str = Field(..., min_length=1, max_length=200)
    breed: Optional[str] = Field(None, max_length=100)
    birth_year: Optional[int] = Field(None, ge=1900, le=2100)
    color: Optional[str] = Field(None, max_length=50)
    description: Optional[str] = None
    price: float = Field(..., gt=0)
    location: Optional[str] = Field(None, max_length=200)
    owner_mobile: Optional[str] = Field(None, max_length=20)

    @field_validator('price')
    @classmethod
    def validate_price(cls, v):
        if v <= 0:
            raise ValueError('Price must be greater than 0')
        return v


class UserBullSellUpdate(BaseModel):
    """Schema for updating a user bull listing"""
    name: Optional[str] = Field(None, min_length=1, max_length=200)
    breed: Optional[str] = Field(None, max_length=100)
    birth_year: Optional[int] = Field(None, ge=1900, le=2100)
    color: Optional[str] = Field(None, max_length=50)
    description: Optional[str] = None
    price: Optional[float] = Field(None, gt=0)
    location: Optional[str] = Field(None, max_length=200)
    owner_mobile: Optional[str] = Field(None, max_length=20)
    status: Optional[str] = Field(None, pattern='^(available|sold|expired)$')


class UserBullSellResponse(BaseModel):
    """Schema for user bull listing response"""
    id: UUID
    user_id: UUID
    name: str
    breed: Optional[str]
    birth_year: Optional[int]
    color: Optional[str]
    description: Optional[str]
    price: float
    image_url: str
    location: Optional[str]
    owner_mobile: Optional[str]
    status: str
    created_at: datetime
    updated_at: datetime
    expires_at: datetime
    days_remaining: int

    class Config:
        from_attributes = True


class UserBullSellListResponse(BaseModel):
    """Schema for listing user bulls"""
    bulls: list[UserBullSellResponse]
    total: int
    active_count: int
    max_allowed: int
