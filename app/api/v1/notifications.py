"""
Notification API endpoints
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from typing import List
import logging

from app.db.base import get_db
from app.models.device_token import DeviceToken
from app.schemas.device_token import DeviceTokenCreate, DeviceTokenResponse, DeviceTokenDelete
from app.schemas.notification import SendRaceNotificationRequest, SendRaceNotificationResponse
from app.core.auth import get_current_user_optional
from app.core.dependencies import get_current_active_admin
from app.models.user import User
from app.models.admin import AdminUser

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/register-device", response_model=DeviceTokenResponse, status_code=status.HTTP_201_CREATED)
async def register_device_token(
    token_data: DeviceTokenCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_optional)
):
    """
    Register a device token for push notifications

    - **device_token**: FCM device token
    - **platform**: Device platform (android, ios, web)
    - User can be anonymous (not logged in) or authenticated
    - Automatically subscribes device to 'all_races' topic
    """
    from app.services.firebase_service import firebase_service

    try:
        # Check if token already exists
        existing_token = db.query(DeviceToken).filter(
            DeviceToken.device_token == token_data.device_token
        ).first()

        if existing_token:
            # Update existing token's user_id if user is authenticated
            if current_user and existing_token.user_id != current_user.id:
                existing_token.user_id = current_user.id
                db.commit()
                db.refresh(existing_token)
                logger.info(f"Updated device token {token_data.device_token[:10]}... with user_id: {current_user.id}")

            # Subscribe to 'all_races' topic (idempotent - safe to call multiple times)
            try:
                result = firebase_service.subscribe_to_topic([token_data.device_token], "all_races")
                logger.info(f"✅ Subscribed existing token to 'all_races' topic: {result}")
            except Exception as topic_error:
                logger.warning(f"⚠️ Failed to subscribe to topic (non-critical): {topic_error}")

            return existing_token

        # Create new device token
        new_token = DeviceToken(
            user_id=current_user.id if current_user else None,
            device_token=token_data.device_token,
            platform=token_data.platform
        )

        db.add(new_token)
        db.commit()
        db.refresh(new_token)

        logger.info(f"✅ Registered new device token for platform: {token_data.platform}, user_id: {current_user.id if current_user else 'anonymous'}")

        # Subscribe to 'all_races' topic automatically
        try:
            result = firebase_service.subscribe_to_topic([token_data.device_token], "all_races")
            logger.info(f"✅ Subscribed new token to 'all_races' topic: {result}")
        except Exception as topic_error:
            logger.warning(f"⚠️ Failed to subscribe to topic (non-critical): {topic_error}")

        return new_token

    except IntegrityError as e:
        db.rollback()
        logger.error(f"Database integrity error: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Device token already exists"
        )
    except Exception as e:
        db.rollback()
        logger.error(f"Error registering device token: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to register device token"
        )


@router.delete("/unregister-device", status_code=status.HTTP_204_NO_CONTENT)
async def unregister_device_token(
    token_data: DeviceTokenDelete,
    db: Session = Depends(get_db)
):
    """
    Unregister a device token (call on logout or app uninstall)

    - **device_token**: FCM device token to remove
    """
    try:
        token = db.query(DeviceToken).filter(
            DeviceToken.device_token == token_data.device_token
        ).first()

        if not token:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Device token not found"
            )

        db.delete(token)
        db.commit()

        logger.info(f"✅ Unregistered device token: {token_data.device_token[:10]}...")

        return None

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error unregistering device token: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to unregister device token"
        )


@router.get("/my-devices", response_model=List[DeviceTokenResponse])
async def get_my_devices(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_optional)
):
    """
    Get all device tokens for the current user

    - Requires authentication
    """
    if not current_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required"
        )

    tokens = db.query(DeviceToken).filter(
        DeviceToken.user_id == current_user.id
    ).all()

    return tokens


@router.post("/send-race-notification", response_model=SendRaceNotificationResponse, status_code=status.HTTP_200_OK)
async def send_race_notification(
    request: SendRaceNotificationRequest,
    db: Session = Depends(get_db),
    current_admin: AdminUser = Depends(get_current_active_admin)
):
    """
    Send notification for a specific race to all subscribed users

    - **race_id**: UUID of the race
    - **notification_type**: "one_day_before" or "race_day"
    - **FREE**: Uses Firebase topic messaging (no cost)
    """
    from app.models.race import Race
    from app.services.firebase_service import firebase_service
    from uuid import UUID

    try:
        # Initialize Firebase (only initializes once due to singleton pattern)
        try:
            firebase_service.initialize("gcp-key.json")
        except Exception as firebase_init_error:
            logger.error(f"Firebase initialization error: {firebase_init_error}")
            # If already initialized, this is fine - continue
            if "The default Firebase app already exists" not in str(firebase_init_error):
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=f"Firebase initialization failed: {str(firebase_init_error)}"
                )

        # Get race details
        race = db.query(Race).filter(Race.id == UUID(request.race_id)).first()
        if not race:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Race not found"
            )

        # Prepare notification based on type
        if request.notification_type == "one_day_before":
            title = "🏁 Race Tomorrow!"
            body = f"{race.name} starts tomorrow at {race.address}"
        elif request.notification_type == "race_day":
            title = "🏁 Race Today!"
            body = f"{race.name} is happening today at {race.address}. Good luck!"
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid notification_type. Use 'one_day_before' or 'race_day'"
            )

        # Send to all_races topic (FREE!)
        logger.info(f"Sending notification to topic 'all_races' for race: {race.name}")
        result = firebase_service.send_to_topic(
            topic="all_races",
            title=title,
            body=body,
            data={
                "type": "race_reminder",
                "notification_type": request.notification_type,
                "race_id": str(race.id),
                "race_name": race.name,
                "race_date": str(race.start_date),
                "screen": "race_detail"
            }
        )

        if result:
            logger.info(f"Notification sent successfully for race: {race.name}")
            return {
                "status": "success",
                "message": f"Notification sent to all_races topic",
                "race": race.name,
                "notification_type": request.notification_type
            }
        else:
            logger.error(f"Firebase send_to_topic returned False for race: {race.name}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to send notification. Check server logs for details."
            )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error sending race notification: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )
