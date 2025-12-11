"""
Public APIs for mobile app (no authentication required)
"""
from typing import List, Optional
from uuid import UUID
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, and_

from app.db.base import get_db
from app.models.bull import Bull
from app.models.owner import Owner
from app.models.race import Race, RaceResult
from app.schemas.bull import BullResponse
from app.schemas.race import RaceResponse

router = APIRouter(prefix="/public", tags=["Public APIs"])


# ============================================================================
# PUBLIC BULL APIs
# ============================================================================

@router.get("/bulls", response_model=List[dict])
async def list_bulls_public(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    search: Optional[str] = Query(None),
    db: Session = Depends(get_db)
):
    """
    List bulls with statistics (public)

    Returns bulls with their win statistics for mobile app
    """
    query = db.query(Bull).filter(Bull.is_active == True)

    if search:
        query = query.filter(Bull.name.ilike(f"%{search}%"))

    bulls = query.order_by(Bull.name).offset(skip).limit(limit).all()

    # Get statistics for each bull
    result = []
    for bull in bulls:
        # Count total races
        total_races = db.query(func.count(RaceResult.id)).filter(
            RaceResult.bull_id == bull.id,
            RaceResult.is_disqualified == False
        ).scalar()

        # Count wins (1st place)
        first_place_wins = db.query(func.count(RaceResult.id)).filter(
            RaceResult.bull_id == bull.id,
            RaceResult.position == 1,
            RaceResult.is_disqualified == False
        ).scalar()

        # Get best time
        best_time = db.query(func.min(RaceResult.time_milliseconds)).filter(
            RaceResult.bull_id == bull.id,
            RaceResult.is_disqualified == False
        ).scalar()

        # Get owner name
        owner = db.query(Owner).filter(Owner.id == bull.owner_id).first()

        result.append({
            "id": str(bull.id),
            "name": bull.name,
            "photo_url": bull.photo_url,
            "breed": bull.breed,
            "color": bull.color,
            "birth_year": bull.birth_year,
            "registration_number": bull.registration_number,
            "owner_name": owner.full_name if owner else None,
            "owner_address": owner.address if owner else None,
            "statistics": {
                "total_races": total_races or 0,
                "first_place_wins": first_place_wins or 0,
                "best_time_milliseconds": best_time
            }
        })

    return result


@router.get("/bulls/{bull_id}", response_model=dict)
async def get_bull_detail_public(
    bull_id: UUID,
    db: Session = Depends(get_db)
):
    """Get detailed bull information with statistics (public)"""
    bull = db.query(Bull).filter(
        Bull.id == bull_id,
        Bull.is_active == True
    ).first()

    if not bull:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Bull not found"
        )

    # Get comprehensive statistics
    total_races = db.query(func.count(RaceResult.id)).filter(
        RaceResult.bull_id == bull.id,
        RaceResult.is_disqualified == False
    ).scalar()

    first_place_wins = db.query(func.count(RaceResult.id)).filter(
        RaceResult.bull_id == bull.id,
        RaceResult.position == 1,
        RaceResult.is_disqualified == False
    ).scalar()

    second_place = db.query(func.count(RaceResult.id)).filter(
        RaceResult.bull_id == bull.id,
        RaceResult.position == 2,
        RaceResult.is_disqualified == False
    ).scalar()

    third_place = db.query(func.count(RaceResult.id)).filter(
        RaceResult.bull_id == bull.id,
        RaceResult.position == 3,
        RaceResult.is_disqualified == False
    ).scalar()

    best_time = db.query(func.min(RaceResult.time_milliseconds)).filter(
        RaceResult.bull_id == bull.id,
        RaceResult.is_disqualified == False
    ).scalar()

    avg_time = db.query(func.avg(RaceResult.time_milliseconds)).filter(
        RaceResult.bull_id == bull.id,
        RaceResult.is_disqualified == False
    ).scalar()

    # Get owner details
    owner = db.query(Owner).filter(Owner.id == bull.owner_id).first()

    # Get recent races (last 10)
    recent_results = db.query(RaceResult, Race).join(
        Race, RaceResult.race_id == Race.id
    ).filter(
        RaceResult.bull_id == bull.id,
        Race.status == "completed"
    ).order_by(Race.race_date.desc()).limit(10).all()

    recent_races = [
        {
            "race_id": str(race.id),
            "race_name": race.name,
            "race_date": race.race_date.isoformat(),
            "position": result.position,
            "time_milliseconds": result.time_milliseconds,
            "time_formatted": f"{result.time_milliseconds / 1000:.2f}s" if result.time_milliseconds else None
        }
        for result, race in recent_results
    ]

    return {
        "id": str(bull.id),
        "name": bull.name,
        "photo_url": bull.photo_url,
        "breed": bull.breed,
        "color": bull.color,
        "birth_year": bull.birth_year,
        "registration_number": bull.registration_number,
        "description": bull.description,
        "owner": {
            "id": str(owner.id) if owner else None,
            "name": owner.full_name if owner else None,
            "phone": owner.phone_number if owner else None,
            "address": owner.address if owner else None
        },
        "statistics": {
            "total_races": total_races or 0,
            "first_place_wins": first_place_wins or 0,
            "second_place_wins": second_place or 0,
            "third_place_wins": third_place or 0,
            "best_time_milliseconds": best_time,
            "best_time_formatted": f"{best_time / 1000:.2f}s" if best_time else None,
            "avg_time_milliseconds": int(avg_time) if avg_time else None,
            "avg_time_formatted": f"{avg_time / 1000:.2f}s" if avg_time else None
        },
        "recent_races": recent_races
    }


# ============================================================================
# PUBLIC RACE APIs
# ============================================================================

@router.get("/races", response_model=List[dict])
async def list_races_public(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    status_filter: Optional[str] = Query(None, alias="status"),
    db: Session = Depends(get_db)
):
    """List races (public)"""
    query = db.query(Race)

    if status_filter:
        query = query.filter(Race.status == status_filter)

    races = query.order_by(Race.race_date.desc()).offset(skip).limit(limit).all()

    result = []
    for race in races:
        # Get winner if race is completed
        winner = None
        if race.status == "completed":
            winner_result = db.query(RaceResult, Bull).join(
                Bull, RaceResult.bull_id == Bull.id
            ).filter(
                RaceResult.race_id == race.id,
                RaceResult.position == 1,
                RaceResult.is_disqualified == False
            ).first()

            if winner_result:
                result_obj, bull = winner_result
                winner = {
                    "bull_id": str(bull.id),
                    "bull_name": bull.name,
                    "time_milliseconds": result_obj.time_milliseconds,
                    "time_formatted": f"{result_obj.time_milliseconds / 1000:.2f}s" if result_obj.time_milliseconds else None
                }

        result.append({
            "id": str(race.id),
            "name": race.name,
            "race_date": race.race_date.isoformat(),
            "address": race.address,
            "status": race.status,
            "total_participants": race.total_participants,
            "track_length_meters": race.track_length_meters,
            "winner": winner
        })

    return result


@router.get("/races/{race_id}", response_model=dict)
async def get_race_detail_public(
    race_id: UUID,
    db: Session = Depends(get_db)
):
    """Get detailed race information with results (public)"""
    race = db.query(Race).filter(Race.id == race_id).first()

    if not race:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Race not found"
        )

    # Get all results with bull and owner info
    results = db.query(RaceResult, Bull, Owner).join(
        Bull, RaceResult.bull_id == Bull.id
    ).join(
        Owner, Bull.owner_id == Owner.id
    ).filter(
        RaceResult.race_id == race.id
    ).order_by(RaceResult.position).all()

    race_results = [
        {
            "position": result.position,
            "bull": {
                "id": str(bull.id),
                "name": bull.name,
                "photo_url": bull.photo_url
            },
            "owner_name": owner.full_name,
            "time_milliseconds": result.time_milliseconds,
            "time_formatted": f"{result.time_milliseconds / 1000:.2f}s" if result.time_milliseconds else None,
            "is_disqualified": result.is_disqualified,
            "disqualification_reason": result.disqualification_reason
        }
        for result, bull, owner in results
    ]

    return {
        "id": str(race.id),
        "name": race.name,
        "race_date": race.race_date.isoformat(),
        "description": race.description,
        "address": race.address,
        "status": race.status,
        "total_participants": race.total_participants,
        "track_length_meters": race.track_length_meters,
        "results": race_results
    }


# ============================================================================
# SEARCH APIs
# ============================================================================

@router.get("/search", response_model=dict)
async def search_public(
    q: str = Query(..., min_length=1),
    db: Session = Depends(get_db)
):
    """
    Search across bulls and races (public)

    Returns matching bulls and races based on search query
    """
    search_term = f"%{q}%"

    # Search bulls by name
    bulls = db.query(Bull).filter(
        Bull.is_active == True,
        Bull.name.ilike(search_term)
    ).limit(20).all()

    bull_results = []
    for bull in bulls:
        owner = db.query(Owner).filter(Owner.id == bull.owner_id).first()

        # Get statistics
        total_races = db.query(func.count(RaceResult.id)).filter(
            RaceResult.bull_id == bull.id,
            RaceResult.is_disqualified == False
        ).scalar()

        first_place_wins = db.query(func.count(RaceResult.id)).filter(
            RaceResult.bull_id == bull.id,
            RaceResult.position == 1,
            RaceResult.is_disqualified == False
        ).scalar()

        bull_results.append({
            "type": "bull",
            "id": str(bull.id),
            "name": bull.name,
            "photo_url": bull.photo_url,
            "breed": bull.breed,
            "owner_name": owner.full_name if owner else None,
            "statistics": {
                "total_races": total_races or 0,
                "first_place_wins": first_place_wins or 0
            }
        })

    # Search races by name
    races = db.query(Race).filter(
        Race.name.ilike(search_term)
    ).order_by(Race.race_date.desc()).limit(20).all()

    race_results = []
    for race in races:
        race_results.append({
            "type": "race",
            "id": str(race.id),
            "name": race.name,
            "race_date": race.race_date.isoformat(),
            "address": race.address,
            "status": race.status,
            "total_participants": race.total_participants
        })

    return {
        "query": q,
        "bulls": bull_results,
        "races": race_results,
        "total_results": len(bull_results) + len(race_results)
    }
