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
    start_date: date
    end_date: date
    address: str = Field(..., min_length=1, max_length=500)
    gps_location: Optional[str] = Field(None, max_length=500)
    management_contact: Optional[str] = Field(None, max_length=20)
    track_length: int = Field(200, gt=0)
    track_length_unit: Literal["meters", "feet"] = "meters"
    description: Optional[str] = None


class RaceCreate(RaceBase):
    status: Optional[Literal["scheduled", "in_progress", "completed", "cancelled"]] = "scheduled"


class RaceUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=200)
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    address: Optional[str] = Field(None, min_length=1, max_length=500)
    gps_location: Optional[str] = Field(None, max_length=500)
    management_contact: Optional[str] = Field(None, max_length=20)
    track_length: Optional[int] = Field(None, gt=0)
    track_length_unit: Optional[Literal["meters", "feet"]] = None
    description: Optional[str] = None
    status: Optional[Literal["scheduled", "in_progress", "completed", "cancelled"]] = None


class RaceResponse(RaceBase):
    id: UUID
    status: str
    created_by: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# Race Day Schemas
class RaceDayBase(BaseModel):
    day_number: int = Field(..., gt=0)
    race_date: date
    day_subtitle: Optional[str] = Field(None, max_length=200)


class RaceDayCreate(RaceDayBase):
    race_id: UUID
    status: Optional[Literal["scheduled", "in_progress", "completed", "cancelled"]] = "scheduled"


class RaceDayUpdate(BaseModel):
    day_number: Optional[int] = Field(None, gt=0)
    race_date: Optional[date] = None
    day_subtitle: Optional[str] = Field(None, max_length=200)
    status: Optional[Literal["scheduled", "in_progress", "completed", "cancelled"]] = None


class RaceDayResponse(RaceDayBase):
    id: UUID
    race_id: UUID
    status: str
    total_participants: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# Race Result Schemas
class RaceResultBase(BaseModel):
    race_day_id: UUID
    bull1_id: Optional[UUID] = None
    bull2_id: Optional[UUID] = None
    owner1_id: Optional[UUID] = None
    owner2_id: Optional[UUID] = None
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
