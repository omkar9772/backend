"""
Pydantic schemas for Notifications
"""
from pydantic import BaseModel, Field


class SendRaceNotificationRequest(BaseModel):
    """Schema for sending race notification request"""
    race_id: str = Field(..., description="UUID of the race")
    notification_type: str = Field(
        ...,
        pattern="^(one_day_before|race_day)$",
        description="Type of notification: 'one_day_before' or 'race_day'"
    )

    model_config = {
        "json_schema_extra": {
            "example": {
                "race_id": "123e4567-e89b-12d3-a456-426614174000",
                "notification_type": "one_day_before"
            }
        }
    }


class SendRaceNotificationResponse(BaseModel):
    """Schema for send race notification response"""
    status: str
    message: str
    race: str
    notification_type: str

    model_config = {
        "json_schema_extra": {
            "example": {
                "status": "success",
                "message": "Notification sent to all_races topic",
                "race": "Aamdar Kesari 2025",
                "notification_type": "one_day_before"
            }
        }
    }
