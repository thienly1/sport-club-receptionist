"""
Notification Pydantic Schemas
Request and response models for Notification endpoints
"""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional
from uuid import UUID

from pydantic import BaseModel, EmailStr


# Enums
class NotificationType(str, Enum):
    ESCALATION = "escalation"
    BOOKING_CONFIRMATION = "booking_confirmation"
    BOOKING_REMINDER = "booking_reminder"
    BOOKING_CANCELLATION = "booking_cancellation"
    LEAD_ALERT = "lead_alert"
    FOLLOW_UP_REMINDER = "follow_up_reminder"
    SYSTEM_ALERT = "system_alert"


class NotificationStatus(str, Enum):
    PENDING = "pending"
    SENT = "sent"
    DELIVERED = "delivered"
    FAILED = "failed"
    BOUNCED = "bounced"


class NotificationChannel(str, Enum):
    SMS = "sms"
    EMAIL = "email"
    WEBHOOK = "webhook"
    PUSH = "push"


# Base Notification schema
class NotificationBase(BaseModel):
    """Base Notification schema"""

    notification_type: NotificationType
    channel: NotificationChannel
    message: str
    subject: Optional[str] = None


# Create Notification schema
class NotificationCreate(NotificationBase):
    """Schema for creating a new notification"""

    club_id: UUID
    customer_id: Optional[UUID] = None
    conversation_id: Optional[UUID] = None
    booking_id: Optional[UUID] = None

    recipient_name: Optional[str] = None
    recipient_phone: Optional[str] = None
    recipient_email: Optional[EmailStr] = None

    template_used: Optional[str] = None
    context_data: Dict[str, Any] = {}

    priority: str = "normal"  # low, normal, high, urgent


# Update Notification schema
class NotificationUpdate(BaseModel):
    """Schema for updating a notification"""

    status: Optional[NotificationStatus] = None
    provider_status: Optional[str] = None
    error_message: Optional[str] = None
    sent_at: Optional[datetime] = None
    delivered_at: Optional[datetime] = None
    failed_at: Optional[datetime] = None


# Response Notification schema
class NotificationResponse(NotificationBase):
    """Schema for Notification responses"""

    id: UUID
    club_id: UUID
    customer_id: Optional[UUID]
    conversation_id: Optional[UUID]
    booking_id: Optional[UUID]

    status: NotificationStatus

    recipient_name: Optional[str]
    recipient_phone: Optional[str]
    recipient_email: Optional[str]

    template_used: Optional[str]
    context_data: Dict[str, Any]

    provider: Optional[str]
    provider_message_id: Optional[str]
    provider_status: Optional[str]

    sent_at: Optional[datetime]
    delivered_at: Optional[datetime]
    failed_at: Optional[datetime]

    error_message: Optional[str]
    retry_count: int
    max_retries: int
    next_retry_at: Optional[datetime]

    cost: Optional[float]
    currency: str
    priority: str

    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# List response
class NotificationList(BaseModel):
    """Schema for list of notifications"""

    notifications: List[NotificationResponse]
    total: int
    page: int = 1
    page_size: int = 50


# SMS specific schemas
class SendSMS(BaseModel):
    """Schema for sending an SMS"""

    to_phone: str
    message: str
    priority: str = "normal"


class SMSStatus(BaseModel):
    """Schema for SMS status response"""

    message_id: str
    status: str
    to: str
    sent_at: datetime
