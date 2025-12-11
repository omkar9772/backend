"""
Leaderboard computation service

Computes monthly Top 10 bulls by region based on:
1. Number of 1st place wins (primary ranking)
2. Best time (tie-breaker)
"""
from datetime import date, datetime
from typing import List, Optional
from uuid import UUID

from sqlalchemy import func, and_
from sqlalchemy.orm import Session

from app.models.bull import Bull
from app.models.race import Race, RaceResult
from app.models.region import District, Taluka, Tahsil, Village
from app.models.leaderboard import Leaderboard


def compute_leaderboard_for_month(
    db: Session,
    year: int,
    month: int,
    region_type: str,
    region_id: UUID
) -> List[dict]:
    """
    Compute Top 10 bulls for a specific region and month

    Args:
        db: Database session
        year: Year (e.g., 2025)
        month: Month (1-12)
        region_type: One of 'district', 'taluka', 'tahsil', 'village'
        region_id: UUID of the region

    Returns:
        List of top 10 bulls with statistics
    """
    # Date range for the month
    start_date = date(year, month, 1)
    if month == 12:
        end_date = date(year + 1, 1, 1)
    else:
        end_date = date(year, month + 1, 1)

    # Build query based on region type
    # We need to filter bulls that participated in races in the specified region
    query = db.query(
        Bull.id.label('bull_id'),
        Bull.name.label('bull_name'),
        Bull.photo_url,
        Bull.village_id,
        func.count(
            func.nullif(RaceResult.position == 1, False)
        ).label('total_wins'),
        func.min(RaceResult.time_milliseconds).label('best_time')
    ).join(
        RaceResult, Bull.id == RaceResult.bull_id
    ).join(
        Race, RaceResult.race_id == Race.id
    ).filter(
        Race.race_date >= start_date,
        Race.race_date < end_date,
        Race.status == 'completed',
        RaceResult.is_disqualified == False
    )

    # Apply region filter based on type
    if region_type == 'village':
        query = query.filter(Race.village_id == region_id)
    elif region_type == 'tahsil':
        # Get all villages in this tahsil
        village_ids = db.query(Village.id).filter(Village.tahsil_id == region_id).all()
        village_ids = [v[0] for v in village_ids]
        query = query.filter(Race.village_id.in_(village_ids))
    elif region_type == 'taluka':
        # Get all villages in all tahsils of this taluka
        tahsil_ids = db.query(Tahsil.id).filter(Tahsil.taluka_id == region_id).all()
        tahsil_ids = [t[0] for t in tahsil_ids]
        village_ids = db.query(Village.id).filter(Village.tahsil_id.in_(tahsil_ids)).all()
        village_ids = [v[0] for v in village_ids]
        query = query.filter(Race.village_id.in_(village_ids))
    elif region_type == 'district':
        # Get all villages in all tahsils of all talukas of this district
        taluka_ids = db.query(Taluka.id).filter(Taluka.district_id == region_id).all()
        taluka_ids = [t[0] for t in taluka_ids]
        tahsil_ids = db.query(Tahsil.id).filter(Tahsil.taluka_id.in_(taluka_ids)).all()
        tahsil_ids = [t[0] for t in tahsil_ids]
        village_ids = db.query(Village.id).filter(Village.tahsil_id.in_(tahsil_ids)).all()
        village_ids = [v[0] for v in village_ids]
        query = query.filter(Race.village_id.in_(village_ids))

    # Group by bull and order by wins (desc) then best time (asc)
    results = query.group_by(
        Bull.id, Bull.name, Bull.photo_url, Bull.village_id
    ).order_by(
        func.count(func.nullif(RaceResult.position == 1, False)).desc(),
        func.min(RaceResult.time_milliseconds).asc()
    ).limit(10).all()

    # Format results
    top_bulls = []
    for rank, result in enumerate(results, start=1):
        # Count total races participated
        total_races = db.query(func.count(RaceResult.id)).join(
            Race, RaceResult.race_id == Race.id
        ).filter(
            RaceResult.bull_id == result.bull_id,
            Race.race_date >= start_date,
            Race.race_date < end_date,
            Race.status == 'completed',
            RaceResult.is_disqualified == False
        ).scalar()

        top_bulls.append({
            'rank': rank,
            'bull_id': result.bull_id,
            'bull_name': result.bull_name,
            'photo_url': result.photo_url,
            'village_id': result.village_id,
            'total_wins': result.total_wins or 0,
            'total_races': total_races or 0,
            'best_time_milliseconds': result.best_time
        })

    return top_bulls


def save_leaderboard_to_db(
    db: Session,
    year: int,
    month: int,
    region_type: str,
    region_id: UUID,
    top_bulls: List[dict]
) -> None:
    """
    Save computed leaderboard to database

    Replaces existing leaderboard for the same month/region
    """
    # Delete existing leaderboard entries for this month/region
    db.query(Leaderboard).filter(
        Leaderboard.year == year,
        Leaderboard.month == month,
        Leaderboard.region_type == region_type,
        Leaderboard.region_id == region_id
    ).delete()

    # Insert new entries
    for bull_data in top_bulls:
        leaderboard_entry = Leaderboard(
            year=year,
            month=month,
            region_type=region_type,
            region_id=region_id,
            bull_id=bull_data['bull_id'],
            rank=bull_data['rank'],
            first_place_wins=bull_data['total_wins'],
            total_races=bull_data['total_races'],
            best_time_milliseconds=bull_data['best_time_milliseconds']
        )
        db.add(leaderboard_entry)

    db.commit()


def compute_and_save_leaderboard(
    db: Session,
    year: int,
    month: int,
    region_type: str,
    region_id: UUID
) -> List[dict]:
    """
    Compute and save leaderboard in one operation

    Returns the computed leaderboard
    """
    top_bulls = compute_leaderboard_for_month(db, year, month, region_type, region_id)
    if top_bulls:
        save_leaderboard_to_db(db, year, month, region_type, region_id, top_bulls)
    return top_bulls


def get_leaderboard_from_db(
    db: Session,
    year: int,
    month: int,
    region_type: str,
    region_id: UUID
) -> List[dict]:
    """
    Retrieve leaderboard from database

    Returns cached leaderboard if available, otherwise computes fresh
    """
    # Try to get from cache
    results = db.query(Leaderboard, Bull).join(
        Bull, Leaderboard.bull_id == Bull.id
    ).filter(
        Leaderboard.year == year,
        Leaderboard.month == month,
        Leaderboard.region_type == region_type,
        Leaderboard.region_id == region_id
    ).order_by(Leaderboard.rank).all()

    if results:
        # Return cached results
        return [
            {
                'rank': leaderboard.rank,
                'bull_id': str(bull.id),
                'bull_name': bull.name,
                'photo_url': bull.photo_url,
                'village_id': str(bull.village_id),
                'total_wins': leaderboard.first_place_wins,
                'total_races': leaderboard.total_races,
                'best_time_milliseconds': leaderboard.best_time_milliseconds,
                'best_time_formatted': f"{leaderboard.best_time_milliseconds / 1000:.2f}s" if leaderboard.best_time_milliseconds else None
            }
            for leaderboard, bull in results
        ]
    else:
        # Compute fresh and save
        top_bulls = compute_and_save_leaderboard(db, year, month, region_type, region_id)
        return [
            {
                **bull,
                'bull_id': str(bull['bull_id']),
                'village_id': str(bull['village_id']),
                'best_time_formatted': f"{bull['best_time_milliseconds'] / 1000:.2f}s" if bull['best_time_milliseconds'] else None
            }
            for bull in top_bulls
        ]


def refresh_all_leaderboards_for_month(db: Session, year: int, month: int) -> int:
    """
    Refresh all leaderboards for a given month

    Useful for batch recomputation after data corrections

    Returns: Number of leaderboards refreshed
    """
    count = 0

    # Refresh for all districts
    districts = db.query(District).all()
    for district in districts:
        compute_and_save_leaderboard(db, year, month, 'district', district.id)
        count += 1

    # Refresh for all talukas
    talukas = db.query(Taluka).all()
    for taluka in talukas:
        compute_and_save_leaderboard(db, year, month, 'taluka', taluka.id)
        count += 1

    # Refresh for all tahsils
    tahsils = db.query(Tahsil).all()
    for tahsil in tahsils:
        compute_and_save_leaderboard(db, year, month, 'tahsil', tahsil.id)
        count += 1

    # Refresh for all villages
    villages = db.query(Village).all()
    for village in villages:
        compute_and_save_leaderboard(db, year, month, 'village', village.id)
        count += 1

    return count
