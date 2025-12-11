"""
Global search endpoint for mobile app
"""
from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy import or_, func
from sqlalchemy.orm import Session

from app.db.base import get_db
from app.models.bull import Bull
from app.models.owner import Owner
from app.models.race import Race

router = APIRouter(prefix="/public/search", tags=["Search"])


@router.get("")
async def global_search(
    q: str = Query(..., min_length=2, description="Search query (minimum 2 characters)"),
    limit: int = Query(10, ge=1, le=50),
    db: Session = Depends(get_db)
):
    """
    Global search across bulls, owners, and races

    Searches:
    - Bull names
    - Owner names
    - Race names

    Args:
        q: Search query string
        limit: Maximum results per category (default 10, max 50)

    Returns:
        Results grouped by category (bulls, owners, races)
    """
    search_pattern = f"%{q}%"

    # Search bulls
    bulls = db.query(Bull).filter(
        Bull.is_active == True,
        Bull.name.ilike(search_pattern)
    ).limit(limit).all()

    bull_results = []
    for bull in bulls:
        # Get owner name
        owner = db.query(Owner).filter(Owner.id == bull.owner_id).first()

        bull_results.append({
            "id": str(bull.id),
            "name": bull.name,
            "photo_url": bull.photo_url,
            "owner_name": owner.full_name if owner else None,
            "type": "bull"
        })

    # Search owners
    owners = db.query(Owner).filter(
        Owner.full_name.ilike(search_pattern)
    ).limit(limit).all()

    owner_results = []
    for owner in owners:
        # Count bulls owned
        bulls_count = db.query(func.count(Bull.id)).filter(
            Bull.owner_id == owner.id,
            Bull.is_active == True
        ).scalar()

        owner_results.append({
            "id": str(owner.id),
            "name": owner.full_name,
            "phone": owner.phone_number,
            "bulls_count": bulls_count,
            "type": "owner"
        })

    # Search races
    races = db.query(Race).filter(
        Race.name.ilike(search_pattern)
    ).order_by(Race.race_date.desc()).limit(limit).all()

    race_results = []
    for race in races:
        race_results.append({
            "id": str(race.id),
            "name": race.name,
            "date": race.race_date.isoformat(),
            "address": race.address,
            "status": race.status,
            "total_participants": race.total_participants,
            "type": "race"
        })

    return {
        "query": q,
        "results": {
            "bulls": bull_results,
            "owners": owner_results,
            "races": race_results
        },
        "total_results": len(bull_results) + len(owner_results) + len(race_results)
    }


@router.get("/bulls")
async def search_bulls(
    q: str = Query(..., min_length=2),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """
    Search bulls only (with more details)

    Args:
        q: Search query
        limit: Max results

    Returns:
        List of bulls matching search
    """
    search_pattern = f"%{q}%"

    query = db.query(Bull).filter(
        Bull.is_active == True,
        Bull.name.ilike(search_pattern)
    )

    bulls = query.limit(limit).all()

    results = []
    for bull in bulls:
        # Get statistics
        from app.models.race import RaceResult

        total_races = db.query(func.count(RaceResult.id)).filter(
            RaceResult.bull_id == bull.id,
            RaceResult.is_disqualified == False
        ).scalar()

        first_place_wins = db.query(func.count(RaceResult.id)).filter(
            RaceResult.bull_id == bull.id,
            RaceResult.position == 1,
            RaceResult.is_disqualified == False
        ).scalar()

        best_time = db.query(func.min(RaceResult.time_milliseconds)).filter(
            RaceResult.bull_id == bull.id,
            RaceResult.is_disqualified == False
        ).scalar()

        # Get owner
        owner = db.query(Owner).filter(Owner.id == bull.owner_id).first()

        results.append({
            "id": str(bull.id),
            "name": bull.name,
            "photo_url": bull.photo_url,
            "breed": bull.breed,
            "color": bull.color,
            "owner_name": owner.full_name if owner else None,
            "statistics": {
                "total_races": total_races or 0,
                "first_place_wins": first_place_wins or 0,
                "best_time_milliseconds": best_time
            }
        })

    return {
        "query": q,
        "results": results,
        "total": len(results)
    }


@router.get("/races")
async def search_races(
    q: str = Query(..., min_length=2),
    status_filter: Optional[str] = Query(None, alias="status"),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """
    Search races only

    Args:
        q: Search query
        status_filter: Optional filter by status
        limit: Max results

    Returns:
        List of races matching search
    """
    search_pattern = f"%{q}%"

    query = db.query(Race).filter(
        Race.name.ilike(search_pattern)
    )

    if status_filter:
        query = query.filter(Race.status == status_filter)

    races = query.order_by(Race.race_date.desc()).limit(limit).all()

    results = []
    for race in races:
        results.append({
            "id": str(race.id),
            "name": race.name,
            "date": race.race_date.isoformat(),
            "address": race.address,
            "status": race.status,
            "total_participants": race.total_participants
        })

    return {
        "query": q,
        "results": results,
        "total": len(results)
    }
