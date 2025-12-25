"""
Race Notification Scheduler

This script sends push notifications for races:
1. One day before race day
2. On race day

Run this script as a cron job twice daily (e.g., at 8 AM and 7 PM)
"""
import sys
import os
from pathlib import Path
from datetime import datetime, date, timedelta
from typing import List
import logging

# Add app directory to Python path
sys.path.insert(0, str(Path(__file__).parent))

from sqlalchemy import create_engine, and_
from sqlalchemy.orm import sessionmaker, Session
from dotenv import load_dotenv

from app.models.race import RaceDay, Race
from app.models.device_token import DeviceToken
from app.services.firebase_service import firebase_service

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('race_notifications.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)


def get_db_session() -> Session:
    """Create database session"""
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        raise ValueError("DATABASE_URL environment variable not set")

    engine = create_engine(database_url)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    return SessionLocal()


def send_notifications_for_tomorrow(db: Session) -> int:
    """
    Send notifications for races happening tomorrow

    Returns:
        int: Number of notifications sent
    """
    tomorrow = date.today() + timedelta(days=1)
    logger.info(f"🔍 Checking for races on {tomorrow}...")

    # Find races happening tomorrow
    race_days = db.query(RaceDay).join(Race).filter(
        and_(
            RaceDay.race_date == tomorrow,
            RaceDay.status == 'scheduled',
            Race.status == 'scheduled'
        )
    ).all()

    if not race_days:
        logger.info(f"📭 No races found for {tomorrow}")
        return 0

    logger.info(f"📬 Found {len(race_days)} race days for {tomorrow}")

    # Get all active device tokens
    tokens = db.query(DeviceToken.device_token).all()
    token_list = [t.device_token for t in tokens]

    if not token_list:
        logger.warning("⚠️ No device tokens found in database")
        return 0

    logger.info(f"📱 Found {len(token_list)} device tokens")

    # Send notifications for each race day
    total_sent = 0
    for race_day in race_days:
        race = race_day.race
        title = f"🏁 Race Tomorrow!"
        body = f"{race.name} starts tomorrow at {race.address}"

        data = {
            "type": "race_reminder",
            "notification_type": "one_day_before",
            "race_id": str(race.id),
            "race_day_id": str(race_day.id),
            "race_name": race.name,
            "race_date": str(race_day.race_date),
            "screen": "race_detail"
        }

        logger.info(f"📤 Sending notification for race: {race.name}")

        # Send to all tokens (using topic for better performance)
        result = firebase_service.send_to_topic(
            topic="all_races",
            title=title,
            body=body,
            data=data
        )

        if result:
            total_sent += 1
            logger.info(f"✅ Notification sent for race: {race.name}")
        else:
            logger.error(f"❌ Failed to send notification for race: {race.name}")

    logger.info(f"📊 Total notifications sent: {total_sent}/{len(race_days)}")
    return total_sent


def send_notifications_for_today(db: Session) -> int:
    """
    Send notifications for races happening today

    Returns:
        int: Number of notifications sent
    """
    today = date.today()
    logger.info(f"🔍 Checking for races on {today}...")

    # Find races happening today
    race_days = db.query(RaceDay).join(Race).filter(
        and_(
            RaceDay.race_date == today,
            RaceDay.status == 'scheduled',
            Race.status == 'scheduled'
        )
    ).all()

    if not race_days:
        logger.info(f"📭 No races found for {today}")
        return 0

    logger.info(f"📬 Found {len(race_days)} race days for {today}")

    # Get all active device tokens
    tokens = db.query(DeviceToken.device_token).all()
    token_list = [t.device_token for t in tokens]

    if not token_list:
        logger.warning("⚠️ No device tokens found in database")
        return 0

    logger.info(f"📱 Found {len(token_list)} device tokens")

    # Send notifications for each race day
    total_sent = 0
    for race_day in race_days:
        race = race_day.race
        title = f"🏁 Race Today!"
        body = f"{race.name} is happening today at {race.address}. Good luck!"

        data = {
            "type": "race_reminder",
            "notification_type": "race_day",
            "race_id": str(race.id),
            "race_day_id": str(race_day.id),
            "race_name": race.name,
            "race_date": str(race_day.race_date),
            "screen": "race_detail"
        }

        logger.info(f"📤 Sending notification for race: {race.name}")

        # Send to all tokens (using topic for better performance)
        result = firebase_service.send_to_topic(
            topic="all_races",
            title=title,
            body=body,
            data=data
        )

        if result:
            total_sent += 1
            logger.info(f"✅ Notification sent for race: {race.name}")
        else:
            logger.error(f"❌ Failed to send notification for race: {race.name}")

    logger.info(f"📊 Total notifications sent: {total_sent}/{len(race_days)}")
    return total_sent


def main():
    """Main function to run the notification scheduler"""
    logger.info("=" * 80)
    logger.info("🚀 Starting Race Notification Scheduler")
    logger.info("=" * 80)

    try:
        # Initialize Firebase
        firebase_credentials_path = os.getenv("FIREBASE_CREDENTIALS_PATH", "gcp-key.json")
        firebase_service.initialize(firebase_credentials_path)

        # Get database session
        db = get_db_session()

        try:
            # Send notifications for tomorrow's races
            logger.info("\n📅 Checking for tomorrow's races...")
            tomorrow_count = send_notifications_for_tomorrow(db)

            # Send notifications for today's races
            logger.info("\n📅 Checking for today's races...")
            today_count = send_notifications_for_today(db)

            logger.info(f"\n✅ Scheduler completed successfully!")
            logger.info(f"   - Tomorrow's races: {tomorrow_count} notifications sent")
            logger.info(f"   - Today's races: {today_count} notifications sent")

        finally:
            db.close()

    except Exception as e:
        logger.error(f"❌ Error running notification scheduler: {e}", exc_info=True)
        sys.exit(1)

    logger.info("=" * 80)


if __name__ == "__main__":
    main()
