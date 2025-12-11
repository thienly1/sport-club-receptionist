"""
Customer Model
Represents potential and new customers contacting the club
"""

import enum
import uuid
from datetime import datetime

from sqlalchemy import Boolean, Column, DateTime
from sqlalchemy import Enum as SQLEnum
from sqlalchemy import ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.database import Base


class CustomerStatus(str, enum.Enum):
    """Customer status in the acquisition funnel"""

    LEAD = "lead"  # First contact, just inquired
    INTERESTED = "interested"  # Expressed interest, asked detailed questions
    TRIAL = "trial"  # Trying out the club (trial membership/session)
    MEMBER = "member"  # Became a member
    INACTIVE = "inactive"  # Lost interest or left


class Customer(Base):
    """
    Customer Model
    Tracks potential and new customers who contact the AI receptionist
    """

    __tablename__ = "customers"

    # Primary Key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Club Association
    club_id = Column(UUID(as_uuid=True), ForeignKey("clubs.id"), nullable=False, index=True)

    # Contact Information
    name = Column(String(255), nullable=False)
    phone = Column(String(20), nullable=False, index=True)
    email = Column(String(255), index=True)

    # Lead Source
    source = Column(String(100))  # phone_call, website, referral, walk_in, etc.

    # Customer Journey
    status = Column(
        SQLEnum(CustomerStatus, values_callable=lambda x: [e.value for e in x]),
        default=CustomerStatus.LEAD,
        index=True,
    )
    # status = Column(SQLEnum(CustomerStatus), default=CustomerStatus.LEAD, index=True)

    # Interests & Preferences
    interested_in = Column(Text)  # What they're interested in: membership, trial, specific sport
    membership_type_interest = Column(String(100))  # Which membership type they asked about
    preferred_contact_method = Column(String(50))  # phone, email, sms

    # Notes from conversations
    notes = Column(Text)  # AI-generated summary or manual notes

    # Flags
    requires_follow_up = Column(Boolean, default=False)
    follow_up_date = Column(DateTime)
    is_high_priority = Column(Boolean, default=False)  # VIP, urgent inquiry, etc.

    # Conversion tracking
    converted_to_member = Column(Boolean, default=False)
    conversion_date = Column(DateTime)

    # Marketing
    consent_marketing = Column(Boolean, default=False)  # Agreed to receive marketing

    # Timestamps
    first_contact_date = Column(DateTime, default=datetime.utcnow)
    last_contact_date = Column(DateTime, default=datetime.utcnow)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    club = relationship("Club", back_populates="customers")
    conversations = relationship("Conversation", back_populates="customer", cascade="all, delete-orphan")
    bookings = relationship("Booking", back_populates="customer", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Customer(name='{self.name}', phone='{self.phone}', status='{self.status}')>"
