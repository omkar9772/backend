"""
Race and RaceResult models
"""
from sqlalchemy import Column, String, Integer, Boolean, ForeignKey, DateTime, Date, Text, CheckConstraint
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID
import uuid
from datetime import datetime

from app.db.base import Base


class Race(Base):
    __tablename__ = "races"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(200), nullable=False)
    race_date = Column(Date, nullable=False)
    address = Column(Text, nullable=False)
    gps_location = Column(String(500), nullable=True)
    management_contact = Column(String(20), nullable=True)
    track_length_meters = Column(Integer, nullable=False, default=200)
    description = Column(Text, nullable=True)
    status = Column(
        String(20),
        default="scheduled",
        nullable=False
    )
    total_participants = Column(Integer, default=0)
    created_by = Column(String(100), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    results = relationship("RaceResult", back_populates="race", cascade="all, delete-orphan")

    # Check constraint for status
    __table_args__ = (
        CheckConstraint(
            "status IN ('scheduled', 'in_progress', 'completed', 'cancelled')",
            name="check_race_status"
        ),
    )

    def __repr__(self):
        return f"<Race(id={self.id}, name='{self.name}', date={self.race_date}, address='{self.address}', status='{self.status}')>"


class RaceResult(Base):
    __tablename__ = "race_results"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    race_id = Column(UUID(as_uuid=True), ForeignKey("races.id", ondelete="CASCADE"), nullable=False)
    bull1_id = Column(UUID(as_uuid=True), ForeignKey("bulls.id", ondelete="RESTRICT"), nullable=True)
    bull2_id = Column(UUID(as_uuid=True), ForeignKey("bulls.id", ondelete="RESTRICT"), nullable=True)
    owner1_id = Column(UUID(as_uuid=True), ForeignKey("owners.id", ondelete="RESTRICT"), nullable=True)
    owner2_id = Column(UUID(as_uuid=True), ForeignKey("owners.id", ondelete="RESTRICT"), nullable=True)
    position = Column(Integer, nullable=False)
    time_milliseconds = Column(Integer, nullable=False)
    is_disqualified = Column(Boolean, default=False)
    disqualification_reason = Column(Text, nullable=True)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    race = relationship("Race", back_populates="results")
    bull1 = relationship("Bull", foreign_keys=[bull1_id])
    bull2 = relationship("Bull", foreign_keys=[bull2_id])
    owner1 = relationship("Owner", foreign_keys=[owner1_id])
    owner2 = relationship("Owner", foreign_keys=[owner2_id])

    # Check constraints
    __table_args__ = (
        CheckConstraint("position > 0", name="check_position_positive"),
        CheckConstraint("time_milliseconds > 0", name="check_time_positive"),
    )

    def __repr__(self):
        return f"<RaceResult(id={self.id}, race_id={self.race_id}, bull_id={self.bull_id}, position={self.position})>"
