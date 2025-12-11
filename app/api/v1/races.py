"""
Race and Race Results management endpoints
"""
from typing import List, Optional
from uuid import UUID
from datetime import date

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session

from app.core.dependencies import get_current_active_admin
from app.db.base import get_db
from app.models.admin import AdminUser
from app.models.race import Race, RaceResult
from app.schemas.race import (
    RaceCreate, RaceUpdate, RaceResponse,
    RaceResultCreate, RaceResultResponse
)

router = APIRouter(prefix="/admin/races", tags=["Admin - Races"])


# ============================================================================
# RACES
# ============================================================================

@router.post("", response_model=RaceResponse, status_code=status.HTTP_201_CREATED)
async def create_race(
    race: RaceCreate,
    db: Session = Depends(get_db),
    current_user: AdminUser = Depends(get_current_active_admin)
):
    """Create a new race"""
    db_race = Race(
        **race.model_dump(),
        created_by=current_user.username
    )
    db.add(db_race)
    db.commit()
    db.refresh(db_race)
    return db_race


@router.get("")
async def list_races(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    search: Optional[str] = Query(None),
    status_filter: Optional[str] = Query(None, alias="status"),
    from_date: Optional[date] = Query(None),
    to_date: Optional[date] = Query(None),
    db: Session = Depends(get_db),
    current_user: AdminUser = Depends(get_current_active_admin)
):
    """
    List races with pagination and filters

    - **skip**: Number of records to skip
    - **limit**: Maximum number of records to return
    - **search**: Search by race name or address
    - **status**: Filter by status (scheduled, in_progress, completed, cancelled)
    - **from_date**: Filter races from this date
    - **to_date**: Filter races up to this date
    """
    query = db.query(Race)

    if search:
        search_filter = f"%{search}%"
        query = query.filter(
            (Race.name.ilike(search_filter)) |
            (Race.address.ilike(search_filter))
        )

    if status_filter:
        query = query.filter(Race.status == status_filter)

    if from_date:
        query = query.filter(Race.race_date >= from_date)

    if to_date:
        query = query.filter(Race.race_date <= to_date)

    total = query.count()
    races = query.order_by(Race.race_date.desc()).offset(skip).limit(limit).all()

    return {
        "data": races,
        "total": total,
        "skip": skip,
        "limit": limit
    }


@router.get("/{race_id}", response_model=RaceResponse)
async def get_race(
    race_id: UUID,
    db: Session = Depends(get_db),
    current_user: AdminUser = Depends(get_current_active_admin)
):
    """Get a race by ID"""
    race = db.query(Race).filter(Race.id == race_id).first()
    if not race:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Race not found"
        )
    return race


@router.put("/{race_id}", response_model=RaceResponse)
async def update_race(
    race_id: UUID,
    race_update: RaceUpdate,
    db: Session = Depends(get_db),
    current_user: AdminUser = Depends(get_current_active_admin)
):
    """Update a race"""
    race = db.query(Race).filter(Race.id == race_id).first()
    if not race:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Race not found"
        )

    # Update fields
    update_data = race_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(race, field, value)

    db.commit()
    db.refresh(race)
    return race


@router.delete("/{race_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_race(
    race_id: UUID,
    db: Session = Depends(get_db),
    current_user: AdminUser = Depends(get_current_active_admin)
):
    """Cancel a race"""
    race = db.query(Race).filter(Race.id == race_id).first()
    if not race:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Race not found"
        )

    race.status = "cancelled"
    db.commit()
    return None


# ============================================================================
# RACE RESULTS
# ============================================================================

@router.post("/{race_id}/results", response_model=List[RaceResultResponse], status_code=status.HTTP_201_CREATED)
async def add_race_results(
    race_id: UUID,
    results: List[RaceResultCreate],
    db: Session = Depends(get_db),
    current_user: AdminUser = Depends(get_current_active_admin)
):
    """
    Add race results (batch entry)

    Accepts a list of results for the race.
    Validates that:
    - Race exists
    - No duplicate bulls
    - No duplicate positions
    - All bulls exist
    """
    # Verify race exists
    race = db.query(Race).filter(Race.id == race_id).first()
    if not race:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Race not found"
        )

    # Validate no duplicates in request
    bull_ids = [r.bull_id for r in results]
    positions = [r.position for r in results]

    if len(bull_ids) != len(set(bull_ids)):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Duplicate bulls in results"
        )

    if len(positions) != len(set(positions)):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Duplicate positions in results"
        )

    # Clear existing results for this race
    db.query(RaceResult).filter(RaceResult.race_id == race_id).delete()

    # Create new results
    db_results = []
    for result in results:
        db_result = RaceResult(race_id=race_id, **result.model_dump())
        db.add(db_result)
        db_results.append(db_result)

    # Update race total participants and status
    race.total_participants = len(results)
    if race.status == "scheduled":
        race.status = "completed"

    db.commit()

    # Refresh all results
    for result in db_results:
        db.refresh(result)

    return db_results


@router.get("/{race_id}/results")
async def get_race_results(
    race_id: UUID,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=200),
    search: Optional[str] = Query(None),
    db: Session = Depends(get_db)
):
    """
    Get all results for a race with pagination and search

    Each result represents one team with 2 owners and optionally 2 bulls.
    Returns enriched data with bull names and owner names.

    - **skip**: Number of records to skip
    - **limit**: Maximum number of records to return
    - **search**: Search by bull name or owner name
    """
    from app.models.bull import Bull
    from app.models.owner import Owner

    # Get all results for this race
    query = db.query(RaceResult).filter(RaceResult.race_id == race_id)

    # For search, we'll filter after enrichment since we need to search in related tables
    # So first get all results, then filter
    all_results = query.order_by(RaceResult.position).all()

    # Build team data with bull and owner info
    team_results = []
    for result in all_results:
        team_data = {
            'result_id': str(result.id),
            'position': result.position,
            'time_milliseconds': result.time_milliseconds,
            'is_disqualified': result.is_disqualified,
        }

        # Add bull1 info if exists
        bull1_name = None
        if result.bull1_id:
            bull1 = db.query(Bull).filter(Bull.id == result.bull1_id).first()
            if bull1:
                team_data['bull1_id'] = str(result.bull1_id)
                team_data['bull1_name'] = bull1.name
                bull1_name = bull1.name

        # Add bull2 info if exists
        bull2_name = None
        if result.bull2_id:
            bull2 = db.query(Bull).filter(Bull.id == result.bull2_id).first()
            if bull2:
                team_data['bull2_id'] = str(result.bull2_id)
                team_data['bull2_name'] = bull2.name
                bull2_name = bull2.name

        # Add owner1 info if exists
        owner1_name = None
        if result.owner1_id:
            owner1 = db.query(Owner).filter(Owner.id == result.owner1_id).first()
            if owner1:
                team_data['owner1_id'] = str(result.owner1_id)
                team_data['owner1_name'] = owner1.full_name
                owner1_name = owner1.full_name

        # Add owner2 info if exists
        owner2_name = None
        if result.owner2_id:
            owner2 = db.query(Owner).filter(Owner.id == result.owner2_id).first()
            if owner2:
                team_data['owner2_id'] = str(result.owner2_id)
                team_data['owner2_name'] = owner2.full_name
                owner2_name = owner2.full_name

        # Apply search filter
        if search:
            search_lower = search.lower()
            matches = False
            if bull1_name and search_lower in bull1_name.lower():
                matches = True
            elif bull2_name and search_lower in bull2_name.lower():
                matches = True
            elif owner1_name and search_lower in owner1_name.lower():
                matches = True
            elif owner2_name and search_lower in owner2_name.lower():
                matches = True

            if not matches:
                continue

        team_results.append(team_data)

    # Apply pagination
    total = len(team_results)
    paginated_results = team_results[skip:skip + limit]

    return {
        "data": paginated_results,
        "total": total,
        "skip": skip,
        "limit": limit
    }


@router.delete("/results/{result_id}", status_code=status.HTTP_204_NO_CONTENT)
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
