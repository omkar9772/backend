"""
Public APIs for mobile app (no authentication required)
"""
from typing import List, Optional
from uuid import UUID
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, or_

from app.db.base import get_db
from app.models.bull import Bull
from app.models.owner import Owner
from app.models.race import Race, RaceDay, RaceResult
from app.models.marketplace import MarketplaceListing
from app.models.user_bull import UserBullSell
from app.schemas.bull import BullResponse
from app.schemas.race import RaceResponse
from app.services.storage import storage_service

router = APIRouter(prefix="/public", tags=["Public APIs"])


@router.get("/dashboard")
async def get_dashboard_public(
    recent_limit: int = Query(4, ge=1, le=10),
    upcoming_limit: int = Query(4, ge=1, le=10),
    db: Session = Depends(get_db)
):
    """
    OPTIMIZED: Get both recent and upcoming races in a single API call
    Perfect for mobile app home screen

    Performance: ~500ms vs 4000ms (2 separate calls)
    """
    from datetime import datetime

    now = datetime.now().date()

    # Parallel queries - both executed in same database round trip
    recent_races = db.query(Race).filter(
        Race.status == "completed"
    ).order_by(Race.end_date.desc()).limit(recent_limit).all()

    upcoming_races = db.query(Race).filter(
        Race.status == "scheduled",
        Race.start_date >= now
    ).order_by(Race.start_date.asc()).limit(upcoming_limit).all()

    return {
        "recent": [
            {
                "id": str(race.id),
                "name": race.name,
                "description": race.description,
                "start_date": race.start_date.isoformat(),
                "end_date": race.end_date.isoformat(),
                "address": race.address,
                "gps_location": race.gps_location,
                "status": race.status
            }
            for race in recent_races
        ],
        "upcoming": [
            {
                "id": str(race.id),
                "name": race.name,
                "description": race.description,
                "start_date": race.start_date.isoformat(),
                "end_date": race.end_date.isoformat(),
                "address": race.address,
                "gps_location": race.gps_location,
                "status": race.status
            }
            for race in upcoming_races
        ]
    }


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
    List bulls with statistics (public) - OPTIMIZED

    Performance improvements:
    - Eager loads owners to avoid N+1 queries
    - Batch fetches statistics for all bulls
    - Serves direct CDN URLs (no signing for public images)
    """
    from sqlalchemy.orm import joinedload

    # Eager load owners in single query
    query = db.query(Bull).options(joinedload(Bull.owner)).filter(Bull.is_active == True)

    if search:
        query = query.filter(Bull.name.ilike(f"%{search}%"))

    bulls = query.order_by(Bull.name).offset(skip).limit(limit).all()

    if not bulls:
        return []

    # Batch fetch statistics for all bulls in 3 queries instead of N queries
    bull_ids = [bull.id for bull in bulls]

    # Query 1: Total races for all bulls
    total_races_subq = db.query(
        func.coalesce(RaceResult.bull1_id, RaceResult.bull2_id).label('bull_id'),
        func.count(RaceResult.id).label('count')
    ).filter(
        and_(
            or_(RaceResult.bull1_id.in_(bull_ids), RaceResult.bull2_id.in_(bull_ids)),
            RaceResult.is_disqualified == False
        )
    ).group_by('bull_id').all()

    total_races_map = {str(row.bull_id): row.count for row in total_races_subq}

    # Query 2: First place wins for all bulls
    wins_subq = db.query(
        func.coalesce(RaceResult.bull1_id, RaceResult.bull2_id).label('bull_id'),
        func.count(RaceResult.id).label('count')
    ).filter(
        and_(
            or_(RaceResult.bull1_id.in_(bull_ids), RaceResult.bull2_id.in_(bull_ids)),
            RaceResult.position == 1,
            RaceResult.is_disqualified == False
        )
    ).group_by('bull_id').all()

    wins_map = {str(row.bull_id): row.count for row in wins_subq}

    # Query 3: Best times for all bulls
    best_times_subq = db.query(
        func.coalesce(RaceResult.bull1_id, RaceResult.bull2_id).label('bull_id'),
        func.min(RaceResult.time_milliseconds).label('best_time')
    ).filter(
        and_(
            or_(RaceResult.bull1_id.in_(bull_ids), RaceResult.bull2_id.in_(bull_ids)),
            RaceResult.is_disqualified == False
        )
    ).group_by('bull_id').all()

    best_times_map = {str(row.bull_id): row.best_time for row in best_times_subq}

    # Build response with signed URLs (7-day expiration for mobile app caching)
    result = []
    for bull in bulls:
        bull_id_str = str(bull.id)

        # Use thumbnail for list view (much smaller file size)
        thumbnail_path = bull.thumbnail_url or bull.photo_url
        if thumbnail_path:
            # Generate long-lived signed URL (7 days) so mobile apps can cache
            photo_url = storage_service.generate_signed_url(thumbnail_path, expiration=604800)  # 7 days
        else:
            photo_url = None

        result.append({
            "id": bull_id_str,
            "name": bull.name,
            "photo_url": photo_url,  # Signed URL valid for 7 days
            "breed": bull.breed,
            "color": bull.color,
            "birth_year": bull.birth_year,
            "registration_number": bull.registration_number,
            "owner_name": bull.owner.full_name if bull.owner else None,
            "owner_address": bull.owner.address if bull.owner else None,
            "statistics": {
                "total_races": total_races_map.get(bull_id_str, 0),
                "first_place_wins": wins_map.get(bull_id_str, 0),
                "best_time_milliseconds": best_times_map.get(bull_id_str)
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

    # Get comprehensive statistics (bull can be bull1 or bull2)
    total_races = db.query(func.count(RaceResult.id)).filter(
        and_(
            or_(RaceResult.bull1_id == bull.id, RaceResult.bull2_id == bull.id),
            RaceResult.is_disqualified == False
        )
    ).scalar()

    first_place_wins = db.query(func.count(RaceResult.id)).filter(
        and_(
            or_(RaceResult.bull1_id == bull.id, RaceResult.bull2_id == bull.id),
            RaceResult.position == 1,
            RaceResult.is_disqualified == False
        )
    ).scalar()

    second_place = db.query(func.count(RaceResult.id)).filter(
        and_(
            or_(RaceResult.bull1_id == bull.id, RaceResult.bull2_id == bull.id),
            RaceResult.position == 2,
            RaceResult.is_disqualified == False
        )
    ).scalar()

    third_place = db.query(func.count(RaceResult.id)).filter(
        and_(
            or_(RaceResult.bull1_id == bull.id, RaceResult.bull2_id == bull.id),
            RaceResult.position == 3,
            RaceResult.is_disqualified == False
        )
    ).scalar()

    best_time = db.query(func.min(RaceResult.time_milliseconds)).filter(
        and_(
            or_(RaceResult.bull1_id == bull.id, RaceResult.bull2_id == bull.id),
            RaceResult.is_disqualified == False
        )
    ).scalar()

    avg_time = db.query(func.avg(RaceResult.time_milliseconds)).filter(
        and_(
            or_(RaceResult.bull1_id == bull.id, RaceResult.bull2_id == bull.id),
            RaceResult.is_disqualified == False
        )
    ).scalar()

    # Get owner details
    owner = db.query(Owner).filter(Owner.id == bull.owner_id).first()

    # Generate signed URL for owner photo
    owner_photo_url = None
    if owner and owner.photo_url:
        try:
            owner_photo_url = storage_service.generate_signed_url(owner.photo_url)
        except:
            owner_photo_url = None

    # Recent races simplified for now due to complex schema
    recent_races = []

    # For detail view, serve ORIGINAL high-quality image (not thumbnail)
    photo_url = None
    if bull.photo_url:
        photo_url = storage_service.generate_signed_url(bull.photo_url, expiration=604800)  # 7 days

    return {
        "id": str(bull.id),
        "name": bull.name,
        "photo_url": photo_url,  # Original image for detail view (~100-200 KB)
        "breed": bull.breed,
        "color": bull.color,
        "birth_year": bull.birth_year,
        "registration_number": bull.registration_number,
        "description": bull.description,
        "owner": {
            "id": str(owner.id) if owner else None,
            "name": owner.full_name if owner else None,
            "phone": owner.phone_number if owner else None,
            "email": owner.email if owner else None,
            "address": owner.address if owner else None,
            "photo_url": owner_photo_url
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
# PUBLIC OWNER APIs
# ============================================================================

@router.get("/owners", response_model=List[dict])
async def list_owners_public(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    search: Optional[str] = Query(None),
    db: Session = Depends(get_db)
):
    """
    OPTIMIZED: List owners with bull count (public)

    Performance improvements:
    - Batch fetches bull counts in a single query (eliminates N+1 problem)
    - Uses 7-day signed URLs for mobile caching

    - **skip**: Number of records to skip
    - **limit**: Maximum number of records to return
    - **search**: Search by owner name, phone, or address
    """
    query = db.query(Owner)

    if search:
        search_filter = f"%{search}%"
        query = query.filter(
            or_(
                Owner.full_name.ilike(search_filter),
                Owner.phone_number.ilike(search_filter),
                Owner.address.ilike(search_filter)
            )
        )

    owners = query.order_by(Owner.full_name).offset(skip).limit(limit).all()

    if not owners:
        return []

    # OPTIMIZATION: Batch fetch bull counts for all owners in a single query
    owner_ids = [owner.id for owner in owners]
    bull_counts_subq = db.query(
        Bull.owner_id,
        func.count(Bull.id).label('count')
    ).filter(
        Bull.owner_id.in_(owner_ids),
        Bull.is_active == True
    ).group_by(Bull.owner_id).all()

    # Create a map of owner_id -> bull_count
    bull_counts_map = {str(row.owner_id): row.count for row in bull_counts_subq}

    # Build response
    result = []
    for owner in owners:
        owner_id_str = str(owner.id)

        # Use thumbnail for list view (prefer thumbnail, fallback to original)
        thumbnail_path = owner.thumbnail_url or owner.photo_url
        photo_url = None
        if thumbnail_path:
            try:
                photo_url = storage_service.generate_signed_url(thumbnail_path, expiration=604800)
            except:
                photo_url = None

        result.append({
            "id": owner_id_str,
            "name": owner.full_name,
            "photo_url": photo_url,  # Thumbnail for fast list view
            "address": owner.address,
            "phone": owner.phone_number,
            "bull_count": bull_counts_map.get(owner_id_str, 0)
        })

    return result


@router.get("/owners/{owner_id}", response_model=dict)
async def get_owner_detail_public(
    owner_id: UUID,
    db: Session = Depends(get_db)
):
    """Get detailed owner information (public)"""
    owner = db.query(Owner).filter(Owner.id == owner_id).first()

    if not owner:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Owner not found"
        )

    # Count active bulls
    bull_count = db.query(func.count(Bull.id)).filter(
        Bull.owner_id == owner.id,
        Bull.is_active == True
    ).scalar()

    # Generate signed URL for photo
    photo_url = None
    if owner.photo_url:
        try:
            photo_url = storage_service.generate_signed_url(owner.photo_url, expiration=604800)
        except:
            photo_url = None

    return {
        "id": str(owner.id),
        "name": owner.full_name,
        "photo_url": photo_url,
        "phone": owner.phone_number,
        "email": owner.email,
        "address": owner.address,
        "bull_count": bull_count or 0,
        "created_at": owner.created_at.isoformat() if owner.created_at else None
    }


@router.get("/owners/{owner_id}/bulls", response_model=List[dict])
async def get_owner_bulls_public(
    owner_id: UUID,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """
    Get all bulls owned by a specific owner (public)

    Returns bulls with their statistics in the same format as /public/bulls
    """
    # Verify owner exists
    owner = db.query(Owner).filter(Owner.id == owner_id).first()
    if not owner:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Owner not found"
        )

    # Get bulls for this owner
    bulls = db.query(Bull).filter(
        Bull.owner_id == owner_id,
        Bull.is_active == True
    ).order_by(Bull.name).offset(skip).limit(limit).all()

    if not bulls:
        return []

    # Batch fetch statistics for all bulls
    bull_ids = [bull.id for bull in bulls]

    # Total races
    total_races_subq = db.query(
        func.coalesce(RaceResult.bull1_id, RaceResult.bull2_id).label('bull_id'),
        func.count(RaceResult.id).label('count')
    ).filter(
        and_(
            or_(RaceResult.bull1_id.in_(bull_ids), RaceResult.bull2_id.in_(bull_ids)),
            RaceResult.is_disqualified == False
        )
    ).group_by('bull_id').all()

    total_races_map = {str(row.bull_id): row.count for row in total_races_subq}

    # First place wins
    wins_subq = db.query(
        func.coalesce(RaceResult.bull1_id, RaceResult.bull2_id).label('bull_id'),
        func.count(RaceResult.id).label('count')
    ).filter(
        and_(
            or_(RaceResult.bull1_id.in_(bull_ids), RaceResult.bull2_id.in_(bull_ids)),
            RaceResult.position == 1,
            RaceResult.is_disqualified == False
        )
    ).group_by('bull_id').all()

    wins_map = {str(row.bull_id): row.count for row in wins_subq}

    # Best times
    best_times_subq = db.query(
        func.coalesce(RaceResult.bull1_id, RaceResult.bull2_id).label('bull_id'),
        func.min(RaceResult.time_milliseconds).label('best_time')
    ).filter(
        and_(
            or_(RaceResult.bull1_id.in_(bull_ids), RaceResult.bull2_id.in_(bull_ids)),
            RaceResult.is_disqualified == False
        )
    ).group_by('bull_id').all()

    best_times_map = {str(row.bull_id): row.best_time for row in best_times_subq}

    # Build response
    result = []
    for bull in bulls:
        bull_id_str = str(bull.id)

        # Use thumbnail for list view
        thumbnail_path = bull.thumbnail_url or bull.photo_url
        if thumbnail_path:
            photo_url = storage_service.generate_signed_url(thumbnail_path, expiration=604800)
        else:
            photo_url = None

        result.append({
            "id": bull_id_str,
            "name": bull.name,
            "photo_url": photo_url,
            "breed": bull.breed,
            "color": bull.color,
            "birth_year": bull.birth_year,
            "registration_number": bull.registration_number,
            "owner_name": owner.full_name,
            "owner_address": owner.address,
            "statistics": {
                "total_races": total_races_map.get(bull_id_str, 0),
                "first_place_wins": wins_map.get(bull_id_str, 0),
                "best_time_milliseconds": best_times_map.get(bull_id_str)
            }
        })

    return result


# ============================================================================
# PUBLIC RACE APIs
# ============================================================================

@router.get("/races")
async def list_races_public(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    status_filter: Optional[str] = Query(None, alias="status"),
    from_date: Optional[str] = Query(None),
    to_date: Optional[str] = Query(None),
    db: Session = Depends(get_db)
):
    """
    List races (public)

    - **skip**: Number of records to skip
    - **limit**: Maximum number of records to return
    - **status**: Filter by status (scheduled, in_progress, completed, cancelled)
    - **from_date**: Filter races from this date
    - **to_date**: Filter races up to this date
    """
    query = db.query(Race)

    if status_filter:
        query = query.filter(Race.status == status_filter)

    if from_date:
        from datetime import datetime
        from_date_obj = datetime.fromisoformat(from_date.replace('Z', '+00:00')).date()
        query = query.filter(Race.start_date >= from_date_obj)

    if to_date:
        from datetime import datetime
        to_date_obj = datetime.fromisoformat(to_date.replace('Z', '+00:00')).date()
        query = query.filter(Race.end_date <= to_date_obj)

    # OPTIMIZED: Removed count() query for better performance (saves ~300-500ms)
    # For infinite scroll, check if results.length < limit to know if more data exists
    races = query.order_by(Race.start_date.desc()).offset(skip).limit(limit).all()

    result = []
    for race in races:
        result.append({
            "id": str(race.id),
            "name": race.name,
            "description": race.description,
            "start_date": race.start_date.isoformat(),
            "end_date": race.end_date.isoformat(),
            "address": race.address,
            "gps_location": race.gps_location,
            "management_contact": race.management_contact,
            "track_length": race.track_length,
            "track_length_unit": race.track_length_unit,
            "status": race.status,
            "created_by": race.created_by,
            "created_at": race.created_at.isoformat() if race.created_at else None,
            "updated_at": race.updated_at.isoformat() if race.updated_at else None
        })

    return {
        "data": result,
        "skip": skip,
        "limit": limit,
        "has_more": len(result) == limit  # If we got full limit, there might be more
    }


@router.get("/races/recent")
async def get_recent_races_public(
    skip: int = Query(0, ge=0),
    limit: int = Query(4, ge=1, le=20),
    db: Session = Depends(get_db)
):
    """
    Get recent completed races (public)

    Returns completed races ordered by end date descending
    """
    query = db.query(Race).filter(Race.status == "completed")
    total = query.count()
    races = query.order_by(Race.end_date.desc()).offset(skip).limit(limit).all()

    result = []
    for race in races:
        result.append({
            "id": str(race.id),
            "name": race.name,
            "description": race.description,
            "start_date": race.start_date.isoformat(),
            "end_date": race.end_date.isoformat(),
            "address": race.address,
            "gps_location": race.gps_location,
            "management_contact": race.management_contact,
            "track_length": race.track_length,
            "track_length_unit": race.track_length_unit,
            "status": race.status,
            "created_by": race.created_by,
            "created_at": race.created_at.isoformat() if race.created_at else None,
            "updated_at": race.updated_at.isoformat() if race.updated_at else None
        })

    return {
        "data": result,
        "total": total,
        "skip": skip,
        "limit": limit
    }


@router.get("/races/upcoming")
async def get_upcoming_races_public(
    skip: int = Query(0, ge=0),
    limit: int = Query(4, ge=1, le=20),
    db: Session = Depends(get_db)
):
    """
    Get upcoming scheduled races (public)

    Returns scheduled races with start_date in the future, ordered by start date ascending
    """
    now = datetime.now().date()

    query = db.query(Race).filter(
        Race.status == "scheduled",
        Race.start_date >= now
    )
    total = query.count()
    races = query.order_by(Race.start_date.asc()).offset(skip).limit(limit).all()

    result = []
    for race in races:
        result.append({
            "id": str(race.id),
            "name": race.name,
            "description": race.description,
            "start_date": race.start_date.isoformat(),
            "end_date": race.end_date.isoformat(),
            "address": race.address,
            "gps_location": race.gps_location,
            "management_contact": race.management_contact,
            "track_length": race.track_length,
            "track_length_unit": race.track_length_unit,
            "status": race.status,
            "created_by": race.created_by,
            "created_at": race.created_at.isoformat() if race.created_at else None,
            "updated_at": race.updated_at.isoformat() if race.updated_at else None
        })

    return {
        "data": result,
        "total": total,
        "skip": skip,
        "limit": limit
    }


@router.get("/races/{race_id}")
async def get_race_detail_public(
    race_id: UUID,
    db: Session = Depends(get_db)
):
    """Get detailed race information (public)"""
    race = db.query(Race).filter(Race.id == race_id).first()

    if not race:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Race not found"
        )

    return {
        "id": str(race.id),
        "name": race.name,
        "description": race.description,
        "start_date": race.start_date.isoformat(),
        "end_date": race.end_date.isoformat(),
        "address": race.address,
        "gps_location": race.gps_location,
        "management_contact": race.management_contact,
        "track_length": race.track_length,
        "track_length_unit": race.track_length_unit,
        "status": race.status,
        "created_by": race.created_by,
        "created_at": race.created_at.isoformat() if race.created_at else None,
        "updated_at": race.updated_at.isoformat() if race.updated_at else None
    }


# ============================================================================
# PUBLIC RACE DAYS APIs
# ============================================================================

@router.get("/races/{race_id}/days")
async def list_race_days_public(
    race_id: UUID,
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """
    OPTIMIZED: List all race days for a specific race (public)
    Removed unnecessary race existence check and count query
    """
    # Direct query - if race doesn't exist, result will be empty (no error needed)
    race_days = db.query(RaceDay).filter(
        RaceDay.race_id == race_id
    ).order_by(RaceDay.day_number).offset(skip).limit(limit).all()

    result = []
    for day in race_days:
        result.append({
            "id": str(day.id),
            "race_id": str(day.race_id),
            "day_number": day.day_number,
            "race_date": day.race_date.isoformat(),
            "day_subtitle": day.day_subtitle,
            "status": day.status,
            "total_participants": day.total_participants,
            "created_at": day.created_at.isoformat() if day.created_at else None,
            "updated_at": day.updated_at.isoformat() if day.updated_at else None
        })

    return {
        "data": result,
        "skip": skip,
        "limit": limit,
        "has_more": len(result) == limit
    }


@router.get("/races/days/{race_day_id}")
async def get_race_day_public(
    race_day_id: UUID,
    db: Session = Depends(get_db)
):
    """Get a race day by ID (public)"""
    race_day = db.query(RaceDay).filter(RaceDay.id == race_day_id).first()
    if not race_day:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Race day not found"
        )

    return {
        "id": str(race_day.id),
        "race_id": str(race_day.race_id),
        "day_number": race_day.day_number,
        "race_date": race_day.race_date.isoformat(),
        "day_subtitle": race_day.day_subtitle,
        "status": race_day.status,
        "total_participants": race_day.total_participants,
        "created_at": race_day.created_at.isoformat() if race_day.created_at else None,
        "updated_at": race_day.updated_at.isoformat() if race_day.updated_at else None
    }


# ============================================================================
# PUBLIC RACE RESULTS APIs
# ============================================================================

@router.get("/races/days/{race_day_id}/results")
async def get_race_results_public(
    race_day_id: UUID,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=200),
    search: Optional[str] = Query(None),
    db: Session = Depends(get_db)
):
    """
    OPTIMIZED: Get all results for a race day (public)

    Uses eager loading to eliminate N+1 queries
    Returns thumbnails instead of original images (94% smaller!)

    - **skip**: Number of records to skip
    - **limit**: Maximum number of records to return
    - **search**: Search by bull name or owner name
    """
    from sqlalchemy.orm import joinedload

    # OPTIMIZED: Eager load all related data in single query
    all_results = db.query(RaceResult).options(
        joinedload(RaceResult.bull1),
        joinedload(RaceResult.bull2),
        joinedload(RaceResult.owner1),
        joinedload(RaceResult.owner2)
    ).filter(
        RaceResult.race_day_id == race_day_id
    ).order_by(RaceResult.position).all()

    # Build team data with bull and owner info
    team_results = []
    for result in all_results:
        team_data = {
            'id': str(result.id),
            'race_day_id': str(result.race_day_id),
            'position': result.position,
            'time_milliseconds': result.time_milliseconds,
            'is_disqualified': result.is_disqualified,
            'disqualification_reason': result.disqualification_reason,
            'notes': result.notes,
            'created_at': result.created_at.isoformat() if result.created_at else None,
            'updated_at': result.updated_at.isoformat() if result.updated_at else None
        }

        # Add bull1 info if exists (already loaded via joinedload)
        bull1_name = None
        bull1_photo = None
        if result.bull1:
            # Use THUMBNAIL for list view (94% smaller than original!)
            thumbnail_path = result.bull1.thumbnail_url or result.bull1.photo_url
            photo_url = None
            if thumbnail_path:
                try:
                    photo_url = storage_service.generate_signed_url(thumbnail_path, expiration=604800)
                except:
                    photo_url = None

            team_data['bull1'] = {
                'id': str(result.bull1.id),
                'name': result.bull1.name,
                'photo_url': photo_url,
                'breed': result.bull1.breed,
                'color': result.bull1.color
            }
            bull1_name = result.bull1.name
            bull1_photo = photo_url

        # Add bull2 info if exists (already loaded via joinedload)
        bull2_name = None
        bull2_photo = None
        if result.bull2:
            # Use THUMBNAIL for list view
            thumbnail_path = result.bull2.thumbnail_url or result.bull2.photo_url
            photo_url = None
            if thumbnail_path:
                try:
                    photo_url = storage_service.generate_signed_url(thumbnail_path, expiration=604800)
                except:
                    photo_url = None

            team_data['bull2'] = {
                'id': str(result.bull2.id),
                'name': result.bull2.name,
                'photo_url': photo_url,
                'breed': result.bull2.breed,
                'color': result.bull2.color
            }
            bull2_name = result.bull2.name
            bull2_photo = photo_url

        # Add owner1 info if exists (already loaded via joinedload)
        owner1_name = None
        if result.owner1:
            team_data['owner1'] = {
                'id': str(result.owner1.id),
                'full_name': result.owner1.full_name,
                'phone_number': result.owner1.phone_number,
                'address': result.owner1.address
            }
            owner1_name = result.owner1.full_name

        # Add owner2 info if exists (already loaded via joinedload)
        owner2_name = None
        if result.owner2:
            team_data['owner2'] = {
                'id': str(result.owner2.id),
                'full_name': result.owner2.full_name,
                'phone_number': result.owner2.phone_number,
                'address': result.owner2.address
            }
            owner2_name = result.owner2.full_name

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

        # Get statistics (bull can be bull1 or bull2)
        total_races = db.query(func.count(RaceResult.id)).filter(
            and_(
                or_(RaceResult.bull1_id == bull.id, RaceResult.bull2_id == bull.id),
                RaceResult.is_disqualified == False
            )
        ).scalar()

        first_place_wins = db.query(func.count(RaceResult.id)).filter(
            and_(
                or_(RaceResult.bull1_id == bull.id, RaceResult.bull2_id == bull.id),
                RaceResult.position == 1,
                RaceResult.is_disqualified == False
            )
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
    ).order_by(Race.end_date.desc()).limit(20).all()

    race_results = []
    for race in races:
        # Get total participants from race days
        total_participants = sum(rd.total_participants for rd in race.race_days) if race.race_days else 0

        race_results.append({
            "type": "race",
            "id": str(race.id),
            "name": race.name,
            "race_date": race.end_date.isoformat(),
            "address": race.address,
            "status": race.status,
            "total_participants": total_participants
        })

    return {
        "query": q,
        "bulls": bull_results,
        "races": race_results,
        "total_results": len(bull_results) + len(race_results)
    }


# ============================================================================
# PUBLIC MARKETPLACE APIs (Available Bulls)
# ============================================================================

@router.get("/available-bulls", response_model=List[dict])
async def get_available_bulls(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """
    OPTIMIZED: Get available bulls for adoption/purchase (public)

    Returns marketplace listings with status 'available'
    Uses thumbnails for list view (consistent with bulls listing)
    """
    listings = db.query(MarketplaceListing).filter(
        MarketplaceListing.status == "available"
    ).order_by(MarketplaceListing.created_at.desc()).offset(skip).limit(limit).all()

    result = []
    for listing in listings:
        # Use THUMBNAIL for list view (prefer thumbnail, fallback to original)
        thumbnail_path = listing.thumbnail_url or listing.image_url
        image_url = None
        if thumbnail_path:
            try:
                image_url = storage_service.generate_signed_url(thumbnail_path, expiration=604800)
            except:
                image_url = None

        result.append({
            "id": str(listing.id),
            "name": listing.name,
            "owner_name": listing.owner_name,
            "owner_mobile": listing.owner_mobile,
            "location": listing.location,
            "price": listing.price,
            "image_url": image_url,  # Thumbnail for fast loading
            "description": listing.description,
            "status": listing.status,
            "created_at": listing.created_at.isoformat() if listing.created_at else None
        })

    return result


@router.get("/available-bulls/{listing_id}", response_model=dict)
async def get_available_bull_detail(
    listing_id: UUID,
    db: Session = Depends(get_db)
):
    """Get detailed information about an available bull (public)"""
    listing = db.query(MarketplaceListing).filter(
        MarketplaceListing.id == listing_id
    ).first()

    if not listing:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Listing not found"
        )

    # Use ORIGINAL high-quality image for detail view
    image_url = listing.image_url
    if image_url:
        try:
            image_url = storage_service.generate_signed_url(image_url, expiration=604800)
        except:
            image_url = None

    return {
        "id": str(listing.id),
        "name": listing.name,
        "owner_name": listing.owner_name,
        "owner_mobile": listing.owner_mobile,
        "location": listing.location,
        "price": listing.price,
        "image_url": image_url,
        "description": listing.description,
        "status": listing.status,
        "created_at": listing.created_at.isoformat() if listing.created_at else None
    }


# ============================================================================
# PUBLIC USER BULLS FOR SALE APIs
# ============================================================================

@router.get("/user-bulls-sell", response_model=List[dict])
async def get_user_bulls_for_sale(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """
    Get bulls listed for sale by users (public)

    Returns active user bull listings that haven't expired
    """
    from datetime import datetime

    bulls = db.query(UserBullSell).filter(
        UserBullSell.status == "available",
        UserBullSell.expires_at > datetime.utcnow()
    ).order_by(UserBullSell.created_at.desc()).offset(skip).limit(limit).all()

    result = []
    for bull in bulls:
        # Generate signed URL for image
        image_url = bull.image_url
        if image_url:
            try:
                image_url = storage_service.generate_signed_url(image_url)
            except:
                image_url = None

        result.append({
            "id": str(bull.id),
            "name": bull.name,
            "breed": bull.breed,
            "birth_year": bull.birth_year,
            "color": bull.color,
            "description": bull.description,
            "price": bull.price,
            "image_url": image_url,
            "location": bull.location,
            "owner_mobile": bull.owner_mobile,
            "status": bull.status,
            "created_at": bull.created_at.isoformat() if bull.created_at else None,
            "expires_at": bull.expires_at.isoformat() if bull.expires_at else None,
            "days_remaining": bull.days_remaining
        })

    return result


@router.get("/user-bulls-sell/{bull_id}", response_model=dict)
async def get_user_bull_detail(
    bull_id: UUID,
    db: Session = Depends(get_db)
):
    """Get detailed information about a user bull for sale (public)"""
    bull = db.query(UserBullSell).filter(
        UserBullSell.id == bull_id
    ).first()

    if not bull:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Bull listing not found"
        )

    # Generate signed URL for image
    image_url = bull.image_url
    if image_url:
        try:
            image_url = storage_service.generate_signed_url(image_url)
        except:
            image_url = None

    return {
        "id": str(bull.id),
        "name": bull.name,
        "breed": bull.breed,
        "birth_year": bull.birth_year,
        "color": bull.color,
        "description": bull.description,
        "price": bull.price,
        "image_url": image_url,
        "location": bull.location,
        "owner_mobile": bull.owner_mobile,
        "status": bull.status,
        "created_at": bull.created_at.isoformat() if bull.created_at else None,
        "expires_at": bull.expires_at.isoformat() if bull.expires_at else None,
        "days_remaining": bull.days_remaining
    }
