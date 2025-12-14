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
from app.models.race import Race, RaceDay, RaceResult
from app.schemas.race import (
    RaceCreate, RaceUpdate, RaceResponse,
    RaceDayCreate, RaceDayUpdate, RaceDayResponse,
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
        query = query.filter(Race.start_date >= from_date)

    if to_date:
        query = query.filter(Race.end_date <= to_date)

    total = query.count()
    races = query.order_by(Race.start_date.desc()).offset(skip).limit(limit).all()

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
# RACE DAYS
# ============================================================================

@router.post("/{race_id}/days", response_model=RaceDayResponse, status_code=status.HTTP_201_CREATED)
async def create_race_day(
    race_id: UUID,
    race_day: RaceDayCreate,
    db: Session = Depends(get_db),
    current_user: AdminUser = Depends(get_current_active_admin)
):
    """Create a new race day for a race"""
    # Verify race exists
    race = db.query(Race).filter(Race.id == race_id).first()
    if not race:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Race not found"
        )

    # Verify race_date is within race date range
    if race_day.race_date < race.start_date or race_day.race_date > race.end_date:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Race date must be between {race.start_date} and {race.end_date}"
        )

    # Check if day_number already exists for this race
    existing_day = db.query(RaceDay).filter(
        RaceDay.race_id == race_id,
        RaceDay.day_number == race_day.day_number
    ).first()
    if existing_day:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Day number {race_day.day_number} already exists for this race"
        )

    db_race_day = RaceDay(**race_day.model_dump())
    db.add(db_race_day)
    db.commit()
    db.refresh(db_race_day)
    return db_race_day


@router.get("/{race_id}/days")
async def list_race_days(
    race_id: UUID,
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: AdminUser = Depends(get_current_active_admin)
):
    """List all race days for a specific race"""
    # Verify race exists
    race = db.query(Race).filter(Race.id == race_id).first()
    if not race:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Race not found"
        )

    query = db.query(RaceDay).filter(RaceDay.race_id == race_id)
    total = query.count()
    race_days = query.order_by(RaceDay.day_number).offset(skip).limit(limit).all()

    return {
        "data": race_days,
        "total": total,
        "skip": skip,
        "limit": limit
    }


@router.get("/days/{race_day_id}", response_model=RaceDayResponse)
async def get_race_day(
    race_day_id: UUID,
    db: Session = Depends(get_db),
    current_user: AdminUser = Depends(get_current_active_admin)
):
    """Get a race day by ID"""
    race_day = db.query(RaceDay).filter(RaceDay.id == race_day_id).first()
    if not race_day:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Race day not found"
        )
    return race_day


@router.put("/days/{race_day_id}", response_model=RaceDayResponse)
async def update_race_day(
    race_day_id: UUID,
    race_day_update: RaceDayUpdate,
    db: Session = Depends(get_db),
    current_user: AdminUser = Depends(get_current_active_admin)
):
    """Update a race day"""
    race_day = db.query(RaceDay).filter(RaceDay.id == race_day_id).first()
    if not race_day:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Race day not found"
        )

    # Get the parent race for validation
    race = db.query(Race).filter(Race.id == race_day.race_id).first()

    # Update fields
    update_data = race_day_update.model_dump(exclude_unset=True)

    # Validate race_date if being updated
    if "race_date" in update_data:
        new_date = update_data["race_date"]
        if new_date < race.start_date or new_date > race.end_date:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Race date must be between {race.start_date} and {race.end_date}"
            )

    # Validate day_number if being updated
    if "day_number" in update_data:
        existing_day = db.query(RaceDay).filter(
            RaceDay.race_id == race_day.race_id,
            RaceDay.day_number == update_data["day_number"],
            RaceDay.id != race_day_id
        ).first()
        if existing_day:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Day number {update_data['day_number']} already exists for this race"
            )

    for field, value in update_data.items():
        setattr(race_day, field, value)

    db.commit()
    db.refresh(race_day)
    return race_day


@router.delete("/days/{race_day_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_race_day(
    race_day_id: UUID,
    db: Session = Depends(get_db),
    current_user: AdminUser = Depends(get_current_active_admin)
):
    """Delete a race day"""
    race_day = db.query(RaceDay).filter(RaceDay.id == race_day_id).first()
    if not race_day:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Race day not found"
        )

    db.delete(race_day)
    db.commit()
    return None


# ============================================================================
# RACE RESULTS
# ============================================================================

@router.post("/days/{race_day_id}/results", response_model=List[RaceResultResponse], status_code=status.HTTP_201_CREATED)
async def add_race_results(
    race_day_id: UUID,
    results: List[RaceResultCreate],
    db: Session = Depends(get_db),
    current_user: AdminUser = Depends(get_current_active_admin)
):
    """
    Add race results (batch entry)

    Accepts a list of results for the race day.
    Validates that:
    - Race day exists
    - No duplicate positions
    """
    # Verify race day exists
    race_day = db.query(RaceDay).filter(RaceDay.id == race_day_id).first()
    if not race_day:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Race day not found"
        )

    # Validate no duplicate positions
    positions = [r.position for r in results]

    if len(positions) != len(set(positions)):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Duplicate positions in results"
        )

    # Clear existing results for this race day
    db.query(RaceResult).filter(RaceResult.race_day_id == race_day_id).delete()

    # Create new results
    db_results = []
    for result in results:
        db_result = RaceResult(**result.model_dump())
        db.add(db_result)
        db_results.append(db_result)

    # Update race day total participants and status
    race_day.total_participants = len(results)
    if race_day.status == "scheduled":
        race_day.status = "completed"

    db.commit()

    # Refresh all results
    for result in db_results:
        db.refresh(result)

    return db_results


@router.get("/days/{race_day_id}/results")
async def get_race_results(
    race_day_id: UUID,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=200),
    search: Optional[str] = Query(None),
    db: Session = Depends(get_db)
):
    """
    Get all results for a race day with pagination and search

    Each result represents one team with 2 owners and optionally 2 bulls.
    Returns enriched data with bull names and owner names.

    - **skip**: Number of records to skip
    - **limit**: Maximum number of records to return
    - **search**: Search by bull name or owner name
    """
    from app.models.bull import Bull
    from app.models.owner import Owner

    # Get all results for this race day
    query = db.query(RaceResult).filter(RaceResult.race_day_id == race_day_id)

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


@router.put("/results/{result_id}", response_model=RaceResultResponse)
async def update_race_result(
    result_id: UUID,
    result_data: RaceResultCreate,
    db: Session = Depends(get_db),
    current_user: AdminUser = Depends(get_current_active_admin)
):
    """Update a race result"""
    result = db.query(RaceResult).filter(RaceResult.id == result_id).first()
    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Result not found"
        )

    # Update fields
    for field, value in result_data.model_dump().items():
        setattr(result, field, value)

    db.commit()
    db.refresh(result)
    return result


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
