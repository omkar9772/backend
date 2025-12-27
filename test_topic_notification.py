"""
Test sending notification to 'all_races' topic
This simulates what happens when admin sends a notification
"""
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from app.services.firebase_service import firebase_service
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def test_topic_notification():
    """Send a test notification to 'all_races' topic"""

    # Initialize Firebase
    try:
        firebase_service.initialize("firebase-key.json")
        logger.info("✅ Firebase initialized")
    except Exception as e:
        logger.warning(f"Firebase initialization: {e}")

    try:
        # Send notification to topic (same as admin panel does)
        result = firebase_service.send_to_topic(
            topic="all_races",
            title="🏁 Test Race Notification",
            body="This is a test notification sent to all_races topic. If you see this, EVERYTHING IS WORKING! 🎉",
            data={
                "type": "test",
                "test_id": "topic_test_123"
            }
        )

        if result:
            logger.info("✅✅✅ Topic notification sent successfully!")
            logger.info("   Check your mobile device for the notification")
            logger.info("   This confirms notifications from admin panel will work!")
        else:
            logger.error("❌ Failed to send topic notification")

    except Exception as e:
        logger.error(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    logger.info("🧪 Testing notification to 'all_races' topic...")
    test_topic_notification()
    logger.info("✅ Test complete!")
