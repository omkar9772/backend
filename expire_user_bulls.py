"""
Script to expire old user bull listings

This script should be run daily via a cron job to automatically
expire bull listings that have exceeded their 30-day expiration period.

Usage:
    python expire_user_bulls.py

Cron example (run daily at 2 AM):
    0 2 * * * cd /path/to/backend && python expire_user_bulls.py
"""
import os
import sys
from datetime import datetime
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.models.user_bull import UserBullSell
from app.services.storage import storage_service
from app.core.config import settings


def expire_old_listings():
    """
    Expire user bull listings that have exceeded their expiration date

    This function:
    1. Finds all listings where expires_at < current time and status is 'available'
    2. Updates their status to 'expired'
    3. Optionally deletes images from storage to save space
    """
    # Create database connection
    engine = create_engine(settings.DATABASE_URL)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = SessionLocal()

    try:
        # Find expired listings
        now = datetime.utcnow()
        expired_listings = db.query(UserBullSell).filter(
            UserBullSell.status == 'available',
            UserBullSell.expires_at <= now
        ).all()

        if not expired_listings:
            print(f"[{now}] No expired listings found.")
            return

        print(f"[{now}] Found {len(expired_listings)} expired listings.")

        # Update status to expired
        for listing in expired_listings:
            print(f"  - Expiring listing ID {listing.id}: {listing.name}")
            listing.status = 'expired'
            listing.updated_at = now

            # Optional: Delete image from storage to save space
            # Uncomment the following lines if you want to delete images
            # if listing.image_url:
            #     try:
            #         storage_service.delete_file(listing.image_url)
            #         print(f"    Deleted image: {listing.image_url}")
            #     except Exception as e:
            #         print(f"    Failed to delete image: {e}")

        db.commit()
        print(f"[{now}] Successfully expired {len(expired_listings)} listings.")

    except Exception as e:
        print(f"Error expiring listings: {e}")
        db.rollback()
        raise
    finally:
        db.close()


def delete_old_expired_listings(days_old=60):
    """
    Permanently delete expired listings that are older than specified days

    Args:
        days_old: Number of days after expiration to keep listings (default: 60)

    This is optional cleanup - removes very old expired listings to keep database clean
    """
    from datetime import timedelta

    engine = create_engine(settings.DATABASE_URL)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = SessionLocal()

    try:
        now = datetime.utcnow()
        cutoff_date = now - timedelta(days=days_old)

        old_listings = db.query(UserBullSell).filter(
            UserBullSell.status == 'expired',
            UserBullSell.expires_at <= cutoff_date
        ).all()

        if not old_listings:
            print(f"[{now}] No old expired listings to delete.")
            return

        print(f"[{now}] Found {len(old_listings)} old expired listings to delete.")

        for listing in old_listings:
            print(f"  - Deleting listing ID {listing.id}: {listing.name}")

            # Delete image from storage
            if listing.image_url:
                try:
                    storage_service.delete_file(listing.image_url)
                    print(f"    Deleted image: {listing.image_url}")
                except Exception as e:
                    print(f"    Failed to delete image: {e}")

            db.delete(listing)

        db.commit()
        print(f"[{now}] Successfully deleted {len(old_listings)} old listings.")

    except Exception as e:
        print(f"Error deleting old listings: {e}")
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    print("=" * 60)
    print("User Bulls Expiration Script")
    print("=" * 60)

    # Expire listings that have reached their expiration date
    expire_old_listings()

    # Optional: Delete very old expired listings (older than 60 days)
    # Uncomment the following line if you want to clean up old expired listings
    # delete_old_expired_listings(days_old=60)

    print("=" * 60)
    print("Script completed")
    print("=" * 60)
