"""
Pydantic schemas for Admin User and Authentication
"""
from pydantic import BaseModel, EmailStr, Field
from typing import Optional, Literal
from datetime import datetime
from uuid import UUID


class AdminUserBase(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    email: EmailStr
    full_name: Optional[str] = Field(None, max_length=200)


class AdminUserCreate(AdminUserBase):
    password: str = Field(..., min_length=8)
    role: Literal["super_admin", "admin", "viewer"] = "admin"


class AdminUserResponse(AdminUserBase):
    id: UUID
    role: str
    is_active: bool
    last_login: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class TokenData(BaseModel):
    username: Optional[str] = None
