"""
Pydantic schemas for DeviceToken
"""
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
from uuid import UUID


class DeviceTokenCreate(BaseModel):
    """Schema for creating a new device token"""
    device_token: str = Field(..., min_length=10, max_length=255, description="FCM device token")
    platform: str = Field(..., pattern="^(android|ios|web)$", description="Device platform")

    model_config = {
        "json_schema_extra": {
            "example": {
                "device_token": "fGhI...XyZ",
                "platform": "android"
            }
        }
    }


class DeviceTokenResponse(BaseModel):
    """Schema for device token response"""
    id: UUID
    user_id: Optional[UUID] = None
    device_token: str
    platform: str
    created_at: datetime
    updated_at: datetime

    model_config = {
        "from_attributes": True
    }


class DeviceTokenDelete(BaseModel):
    """Schema for deleting a device token"""
    device_token: str = Field(..., min_length=10, max_length=255, description="FCM device token to delete")

    model_config = {
        "json_schema_extra": {
            "example": {
                "device_token": "fGhI...XyZ"
            }
        }
    }
