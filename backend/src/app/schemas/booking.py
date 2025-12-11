"""
Booking Pydantic Schemas
Request and response models for Booking endpoints
"""

from datetime import datetime
from enum import Enum
from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel, EmailStr


# Enums
class BookingStatus(str, Enum):
    PENDING = "pending"
    CONFIRMED = "confirmed"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    NO_SHOW = "no_show"


class BookingType(str, Enum):
    COURT = "court"
    COACHING = "coaching"
    TRIAL = "trial"
    EVENT = "event"
    OTHER = "other"


# Base Booking schema
class BookingBase(BaseModel):
    """Base Booking schema with common fields"""

    booking_type: BookingType
    resource_name: Optional[str] = None
    description: Optional[str] = None

    booking_date: datetime
    start_time: datetime
    end_time: datetime
    duration_minutes: Optional[int] = None

    contact_name: str
    contact_phone: str
    contact_email: Optional[EmailStr] = None

    notes: Optional[str] = None
    special_requests: Optional[str] = None


class BookingCreate(BookingBase):
    """Schema for creating a new booking"""

    club_id: UUID
    customer_id: UUID
    conversation_id: Optional[UUID] = None

    status: BookingStatus = BookingStatus.PENDING
    booking_type: BookingType = BookingType.COURT
    price: Optional[float] = None
    currency: str = "SEK"
    payment_status: Optional[str] = "pending"


# Update Booking schema
class BookingUpdate(BaseModel):
    """Schema for updating an existing booking"""

    status: Optional[BookingStatus] = None
    booking_type: Optional[BookingType] = None
    resource_name: Optional[str] = None
    description: Optional[str] = None

    booking_date: Optional[datetime] = None
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    duration_minutes: Optional[int] = None

    price: Optional[float] = None
    payment_status: Optional[str] = None

    contact_name: Optional[str] = None
    contact_phone: Optional[str] = None
    contact_email: Optional[EmailStr] = None

    notes: Optional[str] = None
    special_requests: Optional[str] = None

    matchi_booking_id: Optional[str] = None
    cancellation_reason: Optional[str] = None


# Response Booking schema
class BookingResponse(BookingBase):
    """Schema for Booking responses"""

    id: UUID
    club_id: UUID
    customer_id: UUID
    conversation_id: Optional[UUID]

    status: BookingStatus

    price: Optional[float]
    currency: str
    payment_status: Optional[str]

    matchi_booking_id: Optional[str]
    synced_to_matchi: Optional[datetime]

    confirmation_code: Optional[str]
    confirmation_sent_at: Optional[datetime]

    cancellation_reason: Optional[str]
    cancelled_at: Optional[datetime]
    cancelled_by: Optional[str]

    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# List response
class BookingList(BaseModel):
    """Schema for list of bookings"""

    bookings: List[BookingResponse]
    total: int
    page: int = 1
    page_size: int = 50


# Booking confirmation schema
class BookingConfirmation(BaseModel):
    """Schema for booking confirmation"""

    booking_id: UUID
    confirmation_code: str
    message: str
