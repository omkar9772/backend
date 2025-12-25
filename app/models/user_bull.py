"""
User Bulls for Sale model
Allows users to list their bulls for sale with restrictions
"""
from sqlalchemy import Column, String, Integer, Float, DateTime, Text, Index, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import uuid
from datetime import datetime, timedelta

from app.db.base import Base


class UserBullSell(Base):
    __tablename__ = "user_bulls_sell"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True)

    # Bull details
    name = Column(String(200), nullable=False, index=True)
    breed = Column(String(100), nullable=True)
    birth_year = Column(Integer, nullable=True)
    color = Column(String(50), nullable=True)
    description = Column(Text, nullable=True)
    price = Column(Float, nullable=False)
    image_url = Column(String(500), nullable=False)  # URL to GCP Image (original)
    thumbnail_url = Column(String(500), nullable=True)  # Optimized thumbnail for list view
    location = Column(String(200), nullable=True)
    owner_name = Column(String(200), nullable=False)  # Owner's name for contact
    owner_mobile = Column(String(20), nullable=False)  # Owner's mobile for contact

    # Status: 'available', 'sold', 'expired'
    status = Column(String(20), default="available", index=True, nullable=False)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, index=True, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    expires_at = Column(DateTime, nullable=False, index=True)  # 30 days from created_at

    # Relationship
    user = relationship("User", backref="bulls_for_sale")

    __table_args__ = (
        Index('ix_user_bulls_sell_user_status', 'user_id', 'status'),
    )

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # Set expiration to 30 days from now if not set
        if not self.expires_at:
            self.expires_at = datetime.utcnow() + timedelta(days=30)

    def __repr__(self):
        return f"<UserBullSell(id={self.id}, name='{self.name}', user_id={self.user_id})>"

    @property
    def is_expired(self) -> bool:
        """Check if the listing has expired"""
        return datetime.utcnow() > self.expires_at

    @property
    def days_remaining(self) -> int:
        """Get number of days remaining before expiration"""
        if self.is_expired:
            return 0
        delta = self.expires_at - datetime.utcnow()
        return delta.days
