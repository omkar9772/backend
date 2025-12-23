"""
Marketplace Listing models
"""
from sqlalchemy import Column, String, Integer, Float, Boolean, DateTime, Text, Index
from sqlalchemy.dialects.postgresql import UUID
import uuid
from datetime import datetime

from app.db.base import Base

class MarketplaceListing(Base):
    __tablename__ = "marketplace_listings"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(200), nullable=False, index=True)
    owner_name = Column(String(200), nullable=False)
    owner_mobile = Column(String(20), nullable=False)
    location = Column(String(200), nullable=False)
    price = Column(Float, nullable=False)
    image_url = Column(String(500), nullable=False) # URL to GCP Image (original)
    thumbnail_url = Column(String(500), nullable=True) # Optimized thumbnail for list view
    description = Column(Text, nullable=True)
    
    # Status: 'available', 'sold', 'hidden'
    status = Column(String(20), default="available", index=True)
    
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f"<MarketplaceListing(id={self.id}, name='{self.name}', price={self.price})>"
