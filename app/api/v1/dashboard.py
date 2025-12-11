"""
Admin dashboard statistics endpoint
"""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import date, timedelta

from app.core.dependencies import get_current_active_admin
from app.db.base import get_db
from app.models.admin import AdminUser
from app.models.bull import Bull
from app.models.owner import Owner
from app.models.race import Race, RaceResult

router = APIRouter(prefix="/admin/dashboard", tags=["Admin - Dashboard"])


@router.get("/stats")
async def get_dashboard_stats(
    db: Session = Depends(get_db),
    current_user: AdminUser = Depends(get_current_active_admin)
):
    """
    Get dashboard statistics for admin panel

    Returns:
    - Total counts for all entities
    - Monthly statistics
    - Upcoming races
    - Recent activity
    """
    # Total counts
    total_bulls = db.query(func.count(Bull.id)).filter(Bull.is_active == True).scalar()
    total_owners = db.query(func.count(Owner.id)).scalar()
    total_races = db.query(func.count(Race.id)).scalar()

    # This month's races
    today = date.today()
    first_day_of_month = date(today.year, today.month, 1)

    races_this_month = db.query(func.count(Race.id)).filter(
        Race.race_date >= first_day_of_month,
        Race.race_date <= today
    ).scalar()

    # Upcoming races (next 30 days)
    upcoming_races_count = db.query(func.count(Race.id)).filter(
        Race.race_date > today,
        Race.race_date <= today + timedelta(days=30),
        Race.status == "scheduled"
    ).scalar()

    # Get upcoming races
    upcoming_races = db.query(Race).filter(
        Race.race_date > today,
        Race.status == "scheduled"
    ).order_by(Race.race_date).limit(5).all()

    # Recent races
    recent_races = db.query(Race).filter(
        Race.status == "completed"
    ).order_by(Race.race_date.desc()).limit(5).all()

    # Bulls with most wins (top 5)
    top_bulls_subquery = db.query(
        RaceResult.bull_id,
        func.count(RaceResult.id).label('total_wins')
    ).filter(
        RaceResult.position == 1,
        RaceResult.is_disqualified == False
    ).group_by(RaceResult.bull_id).order_by(func.count(RaceResult.id).desc()).limit(5).subquery()

    top_bulls = db.query(Bull).join(
        top_bulls_subquery, Bull.id == top_bulls_subquery.c.bull_id
    ).all()

    return {
        "total_stats": {
            "bulls": total_bulls,
            "owners": total_owners,
            "races": total_races
        },
        "monthly_stats": {
            "races_this_month": races_this_month,
            "upcoming_races": upcoming_races_count
        },
        "upcoming_races": [
            {
                "id": str(race.id),
                "name": race.name,
                "date": race.race_date.isoformat(),
                "address": race.address
            }
            for race in upcoming_races
        ],
        "recent_races": [
            {
                "id": str(race.id),
                "name": race.name,
                "date": race.race_date.isoformat(),
                "participants": race.total_participants,
                "address": race.address
            }
            for race in recent_races
        ],
        "top_bulls": [
            {
                "id": str(bull.id),
                "name": bull.name,
                "owner_id": str(bull.owner_id)
            }
            for bull in top_bulls
        ]
    }
