"""
Notification Model
Tracks notifications sent (SMS to managers, confirmation texts, etc.)
"""

import enum
import uuid
from datetime import datetime

from sqlalchemy import JSON, Column, DateTime
from sqlalchemy import Enum as SQLEnum
from sqlalchemy import Float, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.database import Base


class NotificationType(str, enum.Enum):
    """Type of notification"""

    ESCALATION = "escalation"  # Question escalated to manager
    BOOKING_CONFIRMATION = "booking_confirmation"
    BOOKING_REMINDER = "booking_reminder"
    BOOKING_CANCELLATION = "booking_cancellation"
    LEAD_ALERT = "lead_alert"  # New lead notification to manager
    FOLLOW_UP_REMINDER = "follow_up_reminder"
    SYSTEM_ALERT = "system_alert"


class NotificationStatus(str, enum.Enum):
    """Status of notification"""

    PENDING = "pending"
    SENT = "sent"
    DELIVERED = "delivered"
    FAILED = "failed"
    BOUNCED = "bounced"


class NotificationChannel(str, enum.Enum):
    """Channel used for notification"""

    SMS = "sms"
    EMAIL = "email"
    WEBHOOK = "webhook"
    PUSH = "push"


class Notification(Base):
    """
    Notification Model
    Tracks all notifications sent by the system
    """

    __tablename__ = "notifications"

    # Primary Key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Associations
    club_id = Column(UUID(as_uuid=True), ForeignKey("clubs.id"), nullable=False, index=True)
    customer_id = Column(UUID(as_uuid=True), ForeignKey("customers.id"), index=True)
    conversation_id = Column(UUID(as_uuid=True), ForeignKey("conversations.id"), index=True)
    booking_id = Column(UUID(as_uuid=True), ForeignKey("bookings.id"), index=True)

    # Notification Details
    notification_type = Column(
        SQLEnum(NotificationType, values_callable=lambda x: [e.value for e in x]),
        nullable=False,
        index=True,
    )
    channel = Column(
        SQLEnum(NotificationChannel, values_callable=lambda x: [e.value for e in x]),
        nullable=False,
    )
    status = Column(
        SQLEnum(NotificationStatus, values_callable=lambda x: [e.value for e in x]),
        default=NotificationStatus.PENDING,
        index=True,
    )

    # Recipient
    recipient_name = Column(String(255))
    recipient_phone = Column(String(20))
    recipient_email = Column(String(255))

    # Content
    subject = Column(String(255))  # For emails
    message = Column(Text, nullable=False)
    template_used = Column(String(100))  # Template identifier if used

    # Context data (for template rendering)
    context_data = Column(JSON, default=dict)

    # Provider Details (e.g., Twilio)
    provider = Column(String(50))  # twilio, sendgrid, etc.
    provider_message_id = Column(String(255))  # Provider's tracking ID
    provider_status = Column(String(50))  # Provider-specific status
    provider_response = Column(JSON)  # Full response from provider

    # Delivery tracking
    sent_at = Column(DateTime)
    delivered_at = Column(DateTime)
    failed_at = Column(DateTime)

    # Error handling
    error_message = Column(Text)
    retry_count = Column(Integer, default=0)
    max_retries = Column(Integer, default=3)
    next_retry_at = Column(DateTime)

    # Cost tracking
    cost = Column(Float)  # Cost to send this notification
    currency = Column(String(10), default="SEK")

    # Priority
    priority = Column(String(20), default="normal")  # low, normal, high, urgent

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    club = relationship("Club", back_populates="notifications")
    customer = relationship("Customer")
    conversation = relationship("Conversation")
    booking = relationship("Booking")

    def __repr__(self):
        return f"<Notification(type='{self.notification_type}', channel='{self.channel}', status='{self.status}')>"
