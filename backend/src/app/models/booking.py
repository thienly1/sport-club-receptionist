"""
Booking Model
Tracks bookings made through the AI receptionist (phone bookings)
"""

import enum
import uuid
from datetime import datetime

from sqlalchemy import Column, DateTime
from sqlalchemy import Enum as SQLEnum
from sqlalchemy import Float, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.database import Base


class BookingStatus(str, enum.Enum):
    """Status of booking"""

    PENDING = "pending"  # AI collected info, needs confirmation
    CONFIRMED = "confirmed"  # Booking confirmed
    COMPLETED = "completed"  # Session/booking took place
    CANCELLED = "cancelled"
    NO_SHOW = "no_show"


class BookingType(str, enum.Enum):
    """Type of booking"""

    COURT = "court"  # Court/facility rental
    COACHING = "coaching"  # Coaching session
    TRIAL = "trial"  # Trial session/class
    EVENT = "event"  # Special event
    OTHER = "other"


class Booking(Base):
    """
    Booking Model
    Represents bookings made via phone through the AI receptionist
    Note: Most bookings should still go through Matchi. This is for phone-based bookings.
    """

    __tablename__ = "bookings"

    # Primary Key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Associations
    club_id = Column(UUID(as_uuid=True), ForeignKey("clubs.id"), nullable=False, index=True)
    customer_id = Column(UUID(as_uuid=True), ForeignKey("customers.id"), nullable=False, index=True)
    conversation_id = Column(UUID(as_uuid=True), ForeignKey("conversations.id"), index=True)

    # Booking Details
    booking_type = Column(
        SQLEnum(BookingType, values_callable=lambda x: [e.value for e in x]),
        nullable=False,
    )
    status = Column(
        SQLEnum(BookingStatus, values_callable=lambda x: [e.value for e in x]),
        default=BookingStatus.PENDING,
        index=True,
    )

    # What's being booked
    resource_name = Column(String(255))  # e.g., "Court 1", "Coach Anna", etc.
    description = Column(Text)

    # When
    booking_date = Column(DateTime, nullable=False, index=True)
    start_time = Column(DateTime, nullable=False)
    end_time = Column(DateTime, nullable=False)
    duration_minutes = Column(Integer)

    # Pricing
    price = Column(Float)
    currency = Column(String(10), default="SEK")
    payment_status = Column(String(50))  # pending, paid, refunded

    # Contact for this booking
    contact_name = Column(String(255))
    contact_phone = Column(String(20))
    contact_email = Column(String(255))

    # Special requests/notes
    notes = Column(Text)
    special_requests = Column(Text)

    # Integration
    matchi_booking_id = Column(String(100))  # If synced to Matchi later
    synced_to_matchi = Column(DateTime)

    # Confirmation
    confirmation_code = Column(String(50), unique=True)
    confirmation_sent_at = Column(DateTime)

    # Cancellation
    cancellation_reason = Column(Text)
    cancelled_at = Column(DateTime)
    cancelled_by = Column(String(100))  # customer, club, system

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    club = relationship("Club", back_populates="bookings")
    customer = relationship("Customer", back_populates="bookings")
    conversation = relationship("Conversation")

    def __repr__(self):
        return (
            f"<Booking(id='{self.id}', type='{self.booking_type}', status='{self.status}', date='{self.booking_date}')>"
        )
