"""
Admin User model for authentication
"""
from sqlalchemy import Column, String, Boolean, DateTime, CheckConstraint, Index
from sqlalchemy.dialects.postgresql import UUID
import uuid
from datetime import datetime

from app.db.base import Base


class AdminUser(Base):
    __tablename__ = "admin_users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    username = Column(String(50), nullable=False, unique=True, index=True)
    email = Column(String(255), nullable=False, unique=True, index=True)
    password_hash = Column(String(255), nullable=False)
    full_name = Column(String(200), nullable=True)
    role = Column(String(20), default="admin", nullable=False, index=True)
    is_active = Column(Boolean, default=True, index=True)
    last_login = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Check constraint for role
    __table_args__ = (
        CheckConstraint(
            "role IN ('super_admin', 'admin', 'viewer')",
            name="check_admin_role"
        ),
        Index('ix_admin_users_active_role', 'is_active', 'role'),
    )

    def __repr__(self):
        return f"<AdminUser(id={self.id}, username='{self.username}', role='{self.role}')>"
