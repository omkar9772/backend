"""
Script to manually subscribe all existing device tokens to the 'all_races' topic
Run this once after deploying the backend fixes
"""
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.services.firebase_service import firebase_service
from app.models.device_token import DeviceToken
from app.core.config import settings
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def subscribe_all_tokens():
    """Subscribe all existing device tokens to 'all_races' topic"""

    # Initialize Firebase
    try:
        firebase_service.initialize("firebase-key.json")
        logger.info("✅ Firebase initialized")
    except Exception as e:
        logger.warning(f"Firebase initialization: {e}")

    # Connect to database
    engine = create_engine(settings.DATABASE_URL)
    SessionLocal = sessionmaker(bind=engine)
    db = SessionLocal()

    try:
        # Get all device tokens
        tokens = db.query(DeviceToken).all()

        if not tokens:
            logger.warning("No device tokens found in database")
            return

        logger.info(f"Found {len(tokens)} device token(s)")

        # Extract token strings
        token_strings = [token.device_token for token in tokens]

        # Subscribe to topic
        result = firebase_service.subscribe_to_topic(token_strings, "all_races")

        logger.info(f"✅ Subscription result: {result}")
        logger.info(f"   - Success: {result['success']}")
        logger.info(f"   - Failed: {result['failure']}")

        if result['success'] > 0:
            logger.info("🎉 All tokens successfully subscribed to 'all_races' topic!")

    except Exception as e:
        logger.error(f"❌ Error: {e}")
    finally:
        db.close()


if __name__ == "__main__":
    logger.info("🔔 Subscribing existing device tokens to 'all_races' topic...")
    subscribe_all_tokens()
    logger.info("✅ Done!")
