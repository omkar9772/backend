"""
Race and RaceResult models
"""
from sqlalchemy import Column, String, Integer, Boolean, ForeignKey, DateTime, Date, Text, CheckConstraint, Index
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID
import uuid
from datetime import datetime

from app.db.base import Base


class Race(Base):
    __tablename__ = "races"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(200), nullable=False, index=True)
    start_date = Column(Date, nullable=False, index=True)
    end_date = Column(Date, nullable=False, index=True)
    address = Column(Text, nullable=False)
    gps_location = Column(String(500), nullable=True)
    management_contact = Column(String(20), nullable=True)
    track_length = Column(Integer, nullable=False, default=200)
    track_length_unit = Column(String(10), nullable=False, default="meters")
    description = Column(Text, nullable=True)
    status = Column(
        String(20),
        default="scheduled",
        nullable=False,
        index=True
    )
    created_by = Column(String(100), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    race_days = relationship("RaceDay", back_populates="race", cascade="all, delete-orphan")

    # Check constraints and indexes
    __table_args__ = (
        CheckConstraint(
            "status IN ('scheduled', 'in_progress', 'completed', 'cancelled')",
            name="check_race_status"
        ),
        CheckConstraint(
            "end_date >= start_date",
            name="check_race_dates"
        ),
        CheckConstraint(
            "track_length_unit IN ('meters', 'feet')",
            name="check_track_length_unit"
        ),
        Index('ix_races_status_start_date', 'status', 'start_date'),
        Index('ix_races_dates_range', 'start_date', 'end_date'),
    )

    def __repr__(self):
        return f"<Race(id={self.id}, name='{self.name}', start={self.start_date}, end={self.end_date}, status='{self.status}')>"


class RaceDay(Base):
    __tablename__ = "race_days"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    race_id = Column(UUID(as_uuid=True), ForeignKey("races.id", ondelete="CASCADE"), nullable=False, index=True)
    day_number = Column(Integer, nullable=False, index=True)
    race_date = Column(Date, nullable=False, index=True)
    day_subtitle = Column(String(200), nullable=True)
    status = Column(
        String(20),
        default="scheduled",
        nullable=False,
        index=True
    )
    total_participants = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    race = relationship("Race", back_populates="race_days")
    results = relationship("RaceResult", back_populates="race_day", cascade="all, delete-orphan")

    # Check constraints
    __table_args__ = (
        CheckConstraint(
            "status IN ('scheduled', 'in_progress', 'completed', 'cancelled')",
            name="check_race_day_status"
        ),
        CheckConstraint("day_number > 0", name="check_day_number_positive"),
        Index('ix_race_days_race_day_number', 'race_id', 'day_number', unique=True),
        Index('ix_race_days_race_status', 'race_id', 'status'),
        Index('ix_race_days_date_status', 'race_date', 'status'),
    )

    def __repr__(self):
        return f"<RaceDay(id={self.id}, race_id={self.race_id}, day={self.day_number}, date={self.race_date}, status='{self.status}')>"


class RaceResult(Base):
    __tablename__ = "race_results"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    race_day_id = Column(UUID(as_uuid=True), ForeignKey("race_days.id", ondelete="CASCADE"), nullable=False, index=True)
    bull1_id = Column(UUID(as_uuid=True), ForeignKey("bulls.id", ondelete="RESTRICT"), nullable=True, index=True)
    bull2_id = Column(UUID(as_uuid=True), ForeignKey("bulls.id", ondelete="RESTRICT"), nullable=True, index=True)
    owner1_id = Column(UUID(as_uuid=True), ForeignKey("owners.id", ondelete="RESTRICT"), nullable=True, index=True)
    owner2_id = Column(UUID(as_uuid=True), ForeignKey("owners.id", ondelete="RESTRICT"), nullable=True, index=True)
    position = Column(Integer, nullable=False, index=True)
    time_milliseconds = Column(Integer, nullable=False)
    is_disqualified = Column(Boolean, default=False, index=True)
    disqualification_reason = Column(Text, nullable=True)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    race_day = relationship("RaceDay", back_populates="results")
    bull1 = relationship("Bull", foreign_keys=[bull1_id])
    bull2 = relationship("Bull", foreign_keys=[bull2_id])
    owner1 = relationship("Owner", foreign_keys=[owner1_id])
    owner2 = relationship("Owner", foreign_keys=[owner2_id])

    # Check constraints
    __table_args__ = (
        CheckConstraint("position > 0", name="check_position_positive"),
        CheckConstraint("time_milliseconds > 0", name="check_time_positive"),
        Index('ix_race_results_race_day_position', 'race_day_id', 'position', unique=True),
        Index('ix_race_results_bulls', 'bull1_id', 'bull2_id'),
        Index('ix_race_results_owners', 'owner1_id', 'owner2_id'),
    )

    def __repr__(self):
        return f"<RaceResult(id={self.id}, race_day_id={self.race_day_id}, position={self.position})>"
