"""
Bull model
"""
from sqlalchemy import Column, String, Integer, Boolean, ForeignKey, DateTime, Text, Index
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID
import uuid
from datetime import datetime

from app.db.base import Base


class Bull(Base):
    __tablename__ = "bulls"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(200), nullable=False, index=True)
    owner_id = Column(UUID(as_uuid=True), ForeignKey("owners.id", ondelete="RESTRICT"), nullable=False, index=True)
    birth_year = Column(Integer, nullable=True)
    breed = Column(String(100), nullable=True, index=True)
    color = Column(String(50), nullable=True)
    photo_url = Column(String(500), nullable=True)
    description = Column(Text, nullable=True)
    is_active = Column(Boolean, default=True, index=True)
    registration_number = Column(String(50), unique=True, nullable=True, index=True)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    owner = relationship("Owner", back_populates="bulls")

    __table_args__ = (
        Index('ix_bulls_owner_active', 'owner_id', 'is_active'),
        Index('ix_bulls_name_active', 'name', 'is_active'),
    )

    def __repr__(self):
        return f"<Bull(id={self.id}, name='{self.name}', owner_id={self.owner_id})>"
