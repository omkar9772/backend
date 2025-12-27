"""
Test FCM token directly - send a test notification
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


def test_send_to_token():
    """Send a test notification directly to a token"""

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
        # Get first device token
        token = db.query(DeviceToken).first()

        if not token:
            logger.error("No device tokens found in database")
            return

        logger.info(f"Testing with token: {token.device_token[:50]}...")

        # Send test notification directly to token
        result = firebase_service.send_to_token(
            token=token.device_token,
            title="🧪 Test Notification",
            body="Testing direct notification to your device. If you see this, FCM is working!",
            data={
                "type": "test",
                "test_id": "123"
            }
        )

        if result:
            logger.info("✅ Test notification sent successfully!")
            logger.info("   Check your mobile device for the notification")
        else:
            logger.error("❌ Failed to send test notification")

    except Exception as e:
        logger.error(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()


if __name__ == "__main__":
    logger.info("🧪 Testing direct notification to device token...")
    test_send_to_token()
    logger.info("✅ Test complete!")
