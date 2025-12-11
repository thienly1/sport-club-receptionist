"""
Conversation Models
Tracks conversations between customers and the AI receptionist
"""

import enum
import uuid
from datetime import datetime

from sqlalchemy import JSON, Boolean, Column, DateTime
from sqlalchemy import Enum as SQLEnum
from sqlalchemy import Float, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.database import Base


class ConversationStatus(str, enum.Enum):
    """Status of conversation"""

    ACTIVE = "active"
    COMPLETED = "completed"
    ESCALATED = "escalated"  # Sent to manager
    ABANDONED = "abandoned"


class MessageRole(str, enum.Enum):
    """Who sent the message"""

    CUSTOMER = "customer"
    ASSISTANT = "assistant"
    SYSTEM = "system"


class Conversation(Base):
    """
    Conversation Model
    Represents a complete conversation session with a customer
    """

    __tablename__ = "conversations"

    # Primary Key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Associations
    club_id = Column(UUID(as_uuid=True), ForeignKey("clubs.id"), nullable=False, index=True)
    customer_id = Column(UUID(as_uuid=True), ForeignKey("customers.id"), nullable=False, index=True)

    # VAPI Integration
    vapi_call_id = Column(String(255), unique=True, index=True)  # VAPI's call ID
    vapi_assistant_id = Column(String(255))

    # Call Details
    phone_number = Column(String(20))  # Customer's phone
    call_duration = Column(Integer)  # Duration in seconds
    call_cost = Column(Float)  # Cost in currency units

    # Conversation Metadata
    status = Column(
        SQLEnum(ConversationStatus, values_callable=lambda x: [e.value for e in x]),
        default=ConversationStatus.ACTIVE,
        index=True,
    )
    intent = Column(String(255))  # Main intent: membership_inquiry, booking, information, etc.

    # AI Analysis
    summary = Column(Text)  # AI-generated summary of conversation
    sentiment = Column(String(50))  # positive, neutral, negative
    topics_discussed = Column(JSON, default=list)  # ["membership", "pricing", "facilities"]
    questions_asked = Column(JSON, default=list)  # List of questions customer asked

    # Outcome
    outcome = Column(String(100))  # successful, escalated, needs_follow_up, etc.
    action_required = Column(Text)  # What needs to be done next
    escalated_to_manager = Column(Boolean, default=False)

    # Quality Metrics
    customer_satisfaction = Column(Integer)  # 1-5 rating if collected
    resolution_status = Column(String(50))  # resolved, unresolved, partial

    # Timestamps
    started_at = Column(DateTime, default=datetime.utcnow, index=True)
    ended_at = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    club = relationship("Club", back_populates="conversations")
    customer = relationship("Customer", back_populates="conversations")
    messages = relationship(
        "Message",
        back_populates="conversation",
        cascade="all, delete-orphan",
        order_by="Message.timestamp",
    )

    def __repr__(self):
        return f"<Conversation(id='{self.id}', intent='{self.intent}', status='{self.status}')>"


class Message(Base):
    """
    Message Model
    Individual messages within a conversation
    """

    __tablename__ = "messages"

    # Primary Key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Association
    conversation_id = Column(UUID(as_uuid=True), ForeignKey("conversations.id"), nullable=False, index=True)

    # Message Details
    role = Column(
        SQLEnum(MessageRole, values_callable=lambda x: [e.value for e in x]),
        nullable=False,
    )
    content = Column(Text, nullable=False)

    # Metadata
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)
    duration = Column(Float)  # For audio messages, duration in seconds

    # VAPI specific
    vapi_message_id = Column(String(255))
    function_call = Column(JSON)  # If this message triggered a function call

    # Relationships
    conversation = relationship("Conversation", back_populates="messages")

    def __repr__(self):
        return f"<Message(role='{self.role}', timestamp='{self.timestamp}')>"
