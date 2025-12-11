"""
Pydantic Schemas Package
Exports all request/response schemas
"""

from app.schemas.booking import (
    BookingCreate,
    BookingList,
    BookingResponse,
    BookingStatus,
    BookingType,
    BookingUpdate,
)
from app.schemas.club import (
    ClubCreate,
    ClubList,
    ClubResponse,
    ClubUpdate,
    MembershipType,
    OpeningHours,
    PricingInfo,
)
from app.schemas.conversation import (
    ConversationCreate,
    ConversationList,
    ConversationResponse,
    ConversationStatus,
    ConversationUpdate,
    MessageCreate,
    MessageResponse,
    MessageRole,
)
from app.schemas.customer import (
    CustomerCreate,
    CustomerList,
    CustomerResponse,
    CustomerStatus,
    CustomerUpdate,
)
from app.schemas.notification import (
    NotificationChannel,
    NotificationCreate,
    NotificationList,
    NotificationResponse,
    NotificationStatus,
    NotificationType,
)

__all__ = [
    # Club schemas
    "ClubCreate",
    "ClubUpdate",
    "ClubResponse",
    "ClubList",
    "MembershipType",
    "PricingInfo",
    "OpeningHours",
    # Customer schemas
    "CustomerCreate",
    "CustomerUpdate",
    "CustomerResponse",
    "CustomerList",
    "CustomerStatus",
    # Booking schemas
    "BookingCreate",
    "BookingUpdate",
    "BookingResponse",
    "BookingList",
    "BookingStatus",
    "BookingType",
    # Conversation schemas
    "ConversationCreate",
    "ConversationUpdate",
    "ConversationResponse",
    "ConversationList",
    "MessageCreate",
    "MessageResponse",
    "ConversationStatus",
    "MessageRole",
    # Notification schemas
    "NotificationCreate",
    "NotificationResponse",
    "NotificationList",
    "NotificationType",
    "NotificationStatus",
    "NotificationChannel",
]
