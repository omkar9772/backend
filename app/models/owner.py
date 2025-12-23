"""
Owner model
"""
from sqlalchemy import Column, String, Boolean, ForeignKey, DateTime, Text, Index
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID
import uuid
from datetime import datetime

from app.db.base import Base


class Owner(Base):
    __tablename__ = "owners"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    full_name = Column(String(200), nullable=False, index=True)
    phone_number = Column(String(15), nullable=True, index=True)
    email = Column(String(255), nullable=True, index=True)
    address = Column(Text, nullable=True)
    photo_url = Column(String(500), nullable=True)
    thumbnail_url = Column(String(500), nullable=True)  # Optimized thumbnail for list view
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    bulls = relationship("Bull", back_populates="owner")

    def __repr__(self):
        return f"<Owner(id={self.id}, name='{self.full_name}')>"
