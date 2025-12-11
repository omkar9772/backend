"""
Race Results management endpoints (separate from races)
"""
from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field

from app.core.dependencies import get_current_active_admin
from app.db.base import get_db
from app.models.admin import AdminUser
from app.models.race import Race, RaceResult
from app.models.bull import Bull
from app.models.owner import Owner
from app.schemas.race import RaceResultResponse

router = APIRouter(prefix="/admin/race-results", tags=["Admin - Race Results"])


# Request schema for creating race results (team races)
class CreateRaceResultRequest(BaseModel):
    race_id: UUID
    owner1_id: Optional[UUID] = None
    owner2_id: Optional[UUID] = None
    bull1_id: Optional[UUID] = None
    bull2_id: Optional[UUID] = None
    position: int = Field(..., gt=0)
    time_milliseconds: int = Field(..., gt=0)
    is_disqualified: bool = False


@router.post("", status_code=status.HTTP_201_CREATED)
async def create_race_result(
    request_data: CreateRaceResultRequest,
    db: Session = Depends(get_db),
    current_user: AdminUser = Depends(get_current_active_admin)
):
    """
    Create race result for a team participant

    This endpoint is used by the admin panel to add a team to a race.
    Each team consists of:
    - 2 owners (owner1_id, owner2_id) - can be optional
    - 2 bulls (bull1_id, bull2_id) - optional, can add later if unknown

    Creates a single race result entry representing the team's performance.
    """
    race_id = request_data.race_id
    owner1_id = request_data.owner1_id
    owner2_id = request_data.owner2_id
    bull1_id = request_data.bull1_id
    bull2_id = request_data.bull2_id
    position = request_data.position
    time_milliseconds = request_data.time_milliseconds
    is_disqualified = request_data.is_disqualified

    # Verify race exists
    race = db.query(Race).filter(Race.id == race_id).first()
    if not race:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Race not found"
        )

    # Verify owners exist
    if owner1_id:
        owner1 = db.query(Owner).filter(Owner.id == owner1_id).first()
        if not owner1:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Owner with ID {owner1_id} not found"
            )

    if owner2_id:
        owner2 = db.query(Owner).filter(Owner.id == owner2_id).first()
        if not owner2:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Owner with ID {owner2_id} not found"
            )

    # Verify bulls exist
    if bull1_id:
        bull1 = db.query(Bull).filter(Bull.id == bull1_id).first()
        if not bull1:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Bull with ID {bull1_id} not found"
            )

    if bull2_id:
        bull2 = db.query(Bull).filter(Bull.id == bull2_id).first()
        if not bull2:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Bull with ID {bull2_id} not found"
            )

    # Create a single race result for the team
    # A team consists of 2 owners and optionally 2 bulls
    result = RaceResult(
        race_id=race_id,
        bull1_id=bull1_id,
        bull2_id=bull2_id,
        owner1_id=owner1_id,
        owner2_id=owner2_id,
        position=position,
        time_milliseconds=time_milliseconds,
        is_disqualified=is_disqualified
    )
    db.add(result)

    # Commit the race result first
    db.commit()

    # Update race participant count (count by position)
    from sqlalchemy import func
    team_count = db.query(
        func.count(RaceResult.position)
    ).filter(
        RaceResult.race_id == race_id
    ).scalar()

    race.total_participants = team_count or 0
    db.commit()

    # Refresh the created result
    db.refresh(result)

    return {"message": "Participant added successfully", "result_id": str(result.id)}


@router.get("/{result_id}")
async def get_race_result(
    result_id: UUID,
    db: Session = Depends(get_db),
    current_user: AdminUser = Depends(get_current_active_admin)
):
    """Get a single race result by ID"""
    result = db.query(RaceResult).filter(RaceResult.id == result_id).first()
    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Result not found"
        )

    return {
        "id": str(result.id),
        "race_id": str(result.race_id),
        "bull1_id": str(result.bull1_id) if result.bull1_id else None,
        "bull2_id": str(result.bull2_id) if result.bull2_id else None,
        "owner1_id": str(result.owner1_id) if result.owner1_id else None,
        "owner2_id": str(result.owner2_id) if result.owner2_id else None,
        "position": result.position,
        "time_milliseconds": result.time_milliseconds,
        "is_disqualified": result.is_disqualified
    }


# Request schema for updating race results
class UpdateRaceResultRequest(BaseModel):
    owner1_id: Optional[UUID] = None
    owner2_id: Optional[UUID] = None
    bull1_id: Optional[UUID] = None
    bull2_id: Optional[UUID] = None
    position: int = Field(..., gt=0)
    time_milliseconds: int = Field(..., gt=0)
    is_disqualified: bool = False


@router.put("/{result_id}")
async def update_race_result(
    result_id: UUID,
    request_data: UpdateRaceResultRequest,
    db: Session = Depends(get_db),
    current_user: AdminUser = Depends(get_current_active_admin)
):
    """Update a race result"""
    # Find the result
    result = db.query(RaceResult).filter(RaceResult.id == result_id).first()
    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Result not found"
        )

    # Verify owners exist
    if request_data.owner1_id:
        owner1 = db.query(Owner).filter(Owner.id == request_data.owner1_id).first()
        if not owner1:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Owner with ID {request_data.owner1_id} not found"
            )

    if request_data.owner2_id:
        owner2 = db.query(Owner).filter(Owner.id == request_data.owner2_id).first()
        if not owner2:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Owner with ID {request_data.owner2_id} not found"
            )

    # Verify bulls exist
    if request_data.bull1_id:
        bull1 = db.query(Bull).filter(Bull.id == request_data.bull1_id).first()
        if not bull1:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Bull with ID {request_data.bull1_id} not found"
            )

    if request_data.bull2_id:
        bull2 = db.query(Bull).filter(Bull.id == request_data.bull2_id).first()
        if not bull2:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Bull with ID {request_data.bull2_id} not found"
            )

    # Update the result
    result.bull1_id = request_data.bull1_id
    result.bull2_id = request_data.bull2_id
    result.owner1_id = request_data.owner1_id
    result.owner2_id = request_data.owner2_id
    result.position = request_data.position
    result.time_milliseconds = request_data.time_milliseconds
    result.is_disqualified = request_data.is_disqualified

    db.commit()
    db.refresh(result)

    return {"message": "Participant updated successfully", "result_id": str(result.id)}


@router.delete("/{result_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_race_result(
    result_id: UUID,
    db: Session = Depends(get_db),
    current_user: AdminUser = Depends(get_current_active_admin)
):
    """Delete a race result"""
    result = db.query(RaceResult).filter(RaceResult.id == result_id).first()
    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Result not found"
        )

    db.delete(result)
    db.commit()
    return None
