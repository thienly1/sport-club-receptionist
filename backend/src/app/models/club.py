"""
Club Model
Represents sport clubs using the AI receptionist service
"""

import uuid
from datetime import datetime

from sqlalchemy import JSON, Boolean, Column, DateTime, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.database import Base


class Club(Base):
    """
    Sport Club Model
    Stores information about clubs using the AI receptionist
    """

    __tablename__ = "clubs"

    # Primary Key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Basic Information
    name = Column(String(255), nullable=False, index=True)
    slug = Column(String(255), unique=True, nullable=False, index=True)  # URL-friendly name
    email = Column(String(255), nullable=False, unique=True)
    phone = Column(String(20), nullable=False)

    # Location
    address = Column(Text)
    city = Column(String(100))
    postal_code = Column(String(20))
    country = Column(String(100), default="Sweden")

    # Business Details
    description = Column(Text)
    website = Column(String(255))

    # Matchi Integration
    matchi_club_id = Column(String(100), index=True)  # Their club ID on Matchi
    matchi_booking_url = Column(String(500))  # Direct booking link

    # Membership & Pricing Information (stored as JSON for flexibility)
    membership_types = Column(JSON, default=list)
    # Example: [
    #   {"name": "Individual", "price": 2000, "currency": "SEK", "period": "year"},
    #   {"name": "Family", "price": 3500, "currency": "SEK", "period": "year"}
    # ]

    pricing_info = Column(JSON, default=dict)
    # Example: {
    #   "court_rental": {"indoor": 200, "outdoor": 150, "currency": "SEK", "unit": "hour"},
    #   "coaching": {"group": 300, "private": 600, "currency": "SEK", "unit": "hour"}
    # }

    # Facilities & Amenities
    facilities = Column(JSON, default=list)
    # Example: ["Indoor courts", "Outdoor courts", "Changing rooms", "Cafe", "Pro shop"]

    # Operating Hours (stored as JSON)
    opening_hours = Column(JSON, default=dict)
    # Example: {
    #   "monday": {"open": "06:00", "close": "22:00"},
    #   "tuesday": {"open": "06:00", "close": "22:00"},
    #   ...
    # }

    # Policies & Rules
    policies = Column(Text)  # Free text for policies, cancellation rules, etc.

    # AI Configuration
    ai_assistant_id = Column(String(100))  # VAPI assistant ID for this club
    custom_greeting = Column(Text)  # Custom greeting message
    knowledge_base = Column(JSON, default=dict)  # Custom Q&A pairs

    # VAPI Phone Number
    vapi_phone_number = Column(String(20))  # Dedicated phone number for this club

    # Status
    is_active = Column(Boolean, default=True)
    subscription_tier = Column(String(50), default="basic")  # basic, premium, enterprise

    # Manager Contact (for escalations)
    manager_name = Column(String(255))
    manager_phone = Column(String(20))
    manager_email = Column(String(255))

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    customers = relationship("Customer", back_populates="club", cascade="all, delete-orphan")
    conversations = relationship("Conversation", back_populates="club", cascade="all, delete-orphan")
    bookings = relationship("Booking", back_populates="club", cascade="all, delete-orphan")
    notifications = relationship("Notification", back_populates="club", cascade="all, delete-orphan")
    users = relationship("User", back_populates="club")

    def __repr__(self):
        return f"<Club(name='{self.name}', slug='{self.slug}')>"
