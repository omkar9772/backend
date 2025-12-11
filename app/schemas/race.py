"""
Pydantic schemas for Race and RaceResult
"""
from pydantic import BaseModel, Field
from typing import Optional, Literal
from datetime import datetime, date
from uuid import UUID


# Race Schemas
class RaceBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    race_date: date
    address: str = Field(..., min_length=1, max_length=500)
    gps_location: Optional[str] = Field(None, max_length=500)
    management_contact: Optional[str] = Field(None, max_length=20)
    track_length_meters: int = Field(200, gt=0)
    description: Optional[str] = None


class RaceCreate(RaceBase):
    status: Optional[Literal["scheduled", "in_progress", "completed", "cancelled"]] = "scheduled"


class RaceUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=200)
    race_date: Optional[date] = None
    address: Optional[str] = Field(None, min_length=1, max_length=500)
    gps_location: Optional[str] = Field(None, max_length=500)
    management_contact: Optional[str] = Field(None, max_length=20)
    track_length_meters: Optional[int] = Field(None, gt=0)
    description: Optional[str] = None
    status: Optional[Literal["scheduled", "in_progress", "completed", "cancelled"]] = None


class RaceResponse(RaceBase):
    id: UUID
    status: str
    total_participants: int
    created_by: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# Race Result Schemas
class RaceResultBase(BaseModel):
    race_id: UUID
    bull_id: UUID
    position: int = Field(..., gt=0)
    time_milliseconds: int = Field(..., gt=0)
    is_disqualified: bool = False
    disqualification_reason: Optional[str] = None
    notes: Optional[str] = None


class RaceResultCreate(RaceResultBase):
    pass


class RaceResultResponse(RaceResultBase):
    id: UUID
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
