"""
Firebase Cloud Messaging Service
"""
import firebase_admin
from firebase_admin import credentials, messaging
from pathlib import Path
import logging
from typing import List, Optional, Dict, Any
from datetime import datetime

logger = logging.getLogger(__name__)


class FirebaseService:
    """Service for sending push notifications via Firebase Cloud Messaging"""

    _instance = None
    _initialized = False

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(FirebaseService, cls).__new__(cls)
        return cls._instance

    def initialize(self, credentials_path: Optional[str] = None):
        """
        Initialize Firebase Admin SDK

        Args:
            credentials_path: Path to Firebase service account JSON file
        """
        if self._initialized:
            logger.info("Firebase Admin SDK already initialized")
            return

        try:
            if credentials_path and Path(credentials_path).exists():
                # Initialize with service account file
                cred = credentials.Certificate(credentials_path)
                firebase_admin.initialize_app(cred)
                logger.info(f"✅ Firebase Admin SDK initialized with credentials from {credentials_path}")
            else:
                # Initialize with default credentials (for GCP environment)
                firebase_admin.initialize_app()
                logger.info("✅ Firebase Admin SDK initialized with default credentials")

            self._initialized = True
        except Exception as e:
            logger.error(f"❌ Error initializing Firebase Admin SDK: {e}")
            raise

    def send_to_token(
        self,
        token: str,
        title: str,
        body: str,
        data: Optional[Dict[str, str]] = None
    ) -> bool:
        """
        Send notification to a single device token

        Args:
            token: FCM device token
            title: Notification title
            body: Notification body
            data: Additional data payload

        Returns:
            bool: True if successful, False otherwise
        """
        try:
            message = messaging.Message(
                notification=messaging.Notification(
                    title=title,
                    body=body,
                ),
                data=data or {},
                token=token,
                android=messaging.AndroidConfig(
                    priority='high',
                    notification=messaging.AndroidNotification(
                        sound='default',
                        channel_id='race_notifications',
                    ),
                ),
                apns=messaging.APNSConfig(
                    payload=messaging.APNSPayload(
                        aps=messaging.Aps(
                            sound='default',
                            badge=1,
                        ),
                    ),
                ),
            )

            response = messaging.send(message)
            logger.info(f"✅ Notification sent successfully to token: {token[:10]}... (Message ID: {response})")
            return True

        except messaging.UnregisteredError:
            logger.warning(f"⚠️ Token is no longer valid: {token[:10]}...")
            return False
        except Exception as e:
            logger.error(f"❌ Error sending notification to token {token[:10]}...: {e}")
            return False

    def send_to_tokens(
        self,
        tokens: List[str],
        title: str,
        body: str,
        data: Optional[Dict[str, str]] = None
    ) -> Dict[str, int]:
        """
        Send notification to multiple device tokens (batch)

        Args:
            tokens: List of FCM device tokens
            title: Notification title
            body: Notification body
            data: Additional data payload

        Returns:
            dict: Statistics of success and failure counts
        """
        if not tokens:
            logger.warning("No tokens provided for batch send")
            return {"success": 0, "failure": 0}

        try:
            # Firebase supports up to 500 tokens per batch
            BATCH_SIZE = 500
            success_count = 0
            failure_count = 0

            for i in range(0, len(tokens), BATCH_SIZE):
                batch_tokens = tokens[i:i + BATCH_SIZE]

                message = messaging.MulticastMessage(
                    notification=messaging.Notification(
                        title=title,
                        body=body,
                    ),
                    data=data or {},
                    tokens=batch_tokens,
                    android=messaging.AndroidConfig(
                        priority='high',
                        notification=messaging.AndroidNotification(
                            sound='default',
                            channel_id='race_notifications',
                        ),
                    ),
                    apns=messaging.APNSConfig(
                        payload=messaging.APNSPayload(
                            aps=messaging.Aps(
                                sound='default',
                                badge=1,
                            ),
                        ),
                    ),
                )

                response = messaging.send_multicast(message)
                success_count += response.success_count
                failure_count += response.failure_count

                logger.info(f"✅ Batch notification sent: {response.success_count} succeeded, {response.failure_count} failed")

            logger.info(f"📊 Total notifications sent: {success_count} succeeded, {failure_count} failed out of {len(tokens)} tokens")
            return {"success": success_count, "failure": failure_count}

        except Exception as e:
            logger.error(f"❌ Error sending batch notifications: {e}")
            return {"success": 0, "failure": len(tokens)}

    def send_to_topic(
        self,
        topic: str,
        title: str,
        body: str,
        data: Optional[Dict[str, str]] = None
    ) -> bool:
        """
        Send notification to a topic (all devices subscribed to the topic)

        Args:
            topic: Topic name (e.g., 'all_races')
            title: Notification title
            body: Notification body
            data: Additional data payload

        Returns:
            bool: True if successful, False otherwise
        """
        try:
            message = messaging.Message(
                notification=messaging.Notification(
                    title=title,
                    body=body,
                ),
                data=data or {},
                topic=topic,
                android=messaging.AndroidConfig(
                    priority='high',
                    notification=messaging.AndroidNotification(
                        sound='default',
                        channel_id='race_notifications',
                    ),
                ),
                apns=messaging.APNSConfig(
                    payload=messaging.APNSPayload(
                        aps=messaging.Aps(
                            sound='default',
                            badge=1,
                        ),
                    ),
                ),
            )

            response = messaging.send(message)
            logger.info(f"✅ Notification sent to topic '{topic}' (Message ID: {response})")
            return True

        except Exception as e:
            logger.error(f"❌ Error sending notification to topic '{topic}': {e}")
            return False

    def subscribe_to_topic(self, tokens: List[str], topic: str) -> Dict[str, int]:
        """
        Subscribe device tokens to a topic

        Args:
            tokens: List of FCM device tokens
            topic: Topic name

        Returns:
            dict: Count of successful and failed subscriptions
        """
        try:
            response = messaging.subscribe_to_topic(tokens, topic)
            logger.info(f"✅ Subscribed {response.success_count} tokens to topic '{topic}'")
            return {"success": response.success_count, "failure": response.failure_count}
        except Exception as e:
            logger.error(f"❌ Error subscribing to topic '{topic}': {e}")
            return {"success": 0, "failure": len(tokens)}

    def unsubscribe_from_topic(self, tokens: List[str], topic: str) -> Dict[str, int]:
        """
        Unsubscribe device tokens from a topic

        Args:
            tokens: List of FCM device tokens
            topic: Topic name

        Returns:
            dict: Count of successful and failed unsubscriptions
        """
        try:
            response = messaging.unsubscribe_from_topic(tokens, topic)
            logger.info(f"✅ Unsubscribed {response.success_count} tokens from topic '{topic}'")
            return {"success": response.success_count, "failure": response.failure_count}
        except Exception as e:
            logger.error(f"❌ Error unsubscribing from topic '{topic}': {e}")
            return {"success": 0, "failure": len(tokens)}


# Global instance
firebase_service = FirebaseService()
