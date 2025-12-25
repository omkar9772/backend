"""
Device Token model for storing FCM tokens
"""
from sqlalchemy import Column, String, ForeignKey, DateTime, Index
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import uuid
from datetime import datetime

from app.db.base import Base


class DeviceToken(Base):
    __tablename__ = "device_tokens"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=True, index=True)
    device_token = Column(String(255), unique=True, nullable=False, index=True)
    platform = Column(String(20), nullable=False)  # 'android', 'ios', 'web'
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationship
    user = relationship("User", backref="device_tokens")

    # Indexes
    __table_args__ = (
        Index('ix_device_tokens_user_platform', 'user_id', 'platform'),
    )

    def __repr__(self):
        return f"<DeviceToken(id={self.id}, user_id={self.user_id}, platform='{self.platform}')>"
