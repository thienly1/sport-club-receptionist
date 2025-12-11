"""
Conversation Pydantic Schemas
Request and response models for Conversation and Message endpoints
"""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional
from uuid import UUID

from pydantic import BaseModel, Field


# Enums
class ConversationStatus(str, Enum):
    ACTIVE = "active"
    COMPLETED = "completed"
    ESCALATED = "escalated"
    ABANDONED = "abandoned"


class MessageRole(str, Enum):
    CUSTOMER = "customer"
    ASSISTANT = "assistant"
    SYSTEM = "system"


# Message schemas
class MessageBase(BaseModel):
    """Base Message schema"""

    role: MessageRole
    content: str


class MessageCreate(MessageBase):
    """Schema for creating a new message"""

    conversation_id: UUID
    duration: Optional[float] = None
    vapi_message_id: Optional[str] = None
    function_call: Optional[Dict[str, Any]] = None


class MessageResponse(MessageBase):
    """Schema for Message responses"""

    id: UUID
    conversation_id: UUID
    timestamp: datetime
    duration: Optional[float]
    vapi_message_id: Optional[str]
    function_call: Optional[Dict[str, Any]]

    class Config:
        from_attributes = True


# Conversation schemas
class ConversationBase(BaseModel):
    """Base Conversation schema"""

    phone_number: Optional[str] = None
    intent: Optional[str] = None


class ConversationCreate(ConversationBase):
    """Schema for creating a new conversation"""

    club_id: UUID
    customer_id: UUID
    vapi_call_id: Optional[str] = None
    vapi_assistant_id: Optional[str] = None
    status: ConversationStatus = ConversationStatus.ACTIVE


class ConversationUpdate(BaseModel):
    """Schema for updating an existing conversation"""

    status: Optional[ConversationStatus] = None
    intent: Optional[str] = None

    call_duration: Optional[int] = None
    call_cost: Optional[float] = None

    summary: Optional[str] = None
    sentiment: Optional[str] = None
    topics_discussed: Optional[List[str]] = None
    questions_asked: Optional[List[str]] = None

    outcome: Optional[str] = None
    action_required: Optional[str] = None
    escalated_to_manager: Optional[bool] = None

    customer_satisfaction: Optional[int] = Field(None, ge=1, le=5)
    resolution_status: Optional[str] = None

    ended_at: Optional[datetime] = None


class ConversationResponse(ConversationBase):
    """Schema for Conversation responses"""

    id: UUID
    club_id: UUID
    customer_id: UUID

    vapi_call_id: Optional[str]
    vapi_assistant_id: Optional[str]

    call_duration: Optional[int]
    call_cost: Optional[float]

    status: ConversationStatus

    summary: Optional[str]
    sentiment: Optional[str]
    topics_discussed: List[str]
    questions_asked: List[str]

    outcome: Optional[str]
    action_required: Optional[str]
    escalated_to_manager: bool

    customer_satisfaction: Optional[int]
    resolution_status: Optional[str]

    started_at: datetime
    ended_at: Optional[datetime]
    created_at: datetime
    updated_at: datetime

    # Include messages if requested
    messages: Optional[List[MessageResponse]] = None

    class Config:
        from_attributes = True


class ConversationList(BaseModel):
    """Schema for list of conversations"""

    conversations: List[ConversationResponse]
    total: int
    page: int = 1
    page_size: int = 50


# Detailed conversation with all messages
class ConversationDetail(ConversationResponse):
    """Schema for detailed conversation view with messages"""

    messages: List[MessageResponse]


# VAPI webhook schemas
class VAPICallStarted(BaseModel):
    """Schema for VAPI call started webhook"""

    call_id: str
    phone_number: str
    assistant_id: str
    timestamp: datetime


class VAPICallEnded(BaseModel):
    """Schema for VAPI call ended webhook"""

    call_id: str
    duration: int
    cost: float
    ended_reason: str
    timestamp: datetime


class VAPIMessage(BaseModel):
    """Schema for VAPI message webhook"""

    call_id: str
    message_id: str
    role: str
    content: str
    timestamp: datetime
