"""
Club Pydantic Schemas
Request and response models for Club endpoints
"""

from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field


# Nested schemas for Club fields
class MembershipType(BaseModel):
    """Membership type details"""

    name: str
    price: float
    currency: str = "SEK"
    period: str  # "month", "year", etc.
    description: Optional[str] = None


class PricingInfo(BaseModel):
    """Pricing information"""

    item: str  # e.g., "court_rental", "coaching"
    price: float
    currency: str = "SEK"
    unit: str  # "hour", "session", etc.
    description: Optional[str] = None


class OpeningHours(BaseModel):
    """Opening hours for a day"""

    open: str  # e.g., "06:00"
    close: str  # e.g., "22:00"
    closed: bool = False


# Base Club schema (shared fields)
class ClubBase(BaseModel):
    """Base Club schema with common fields"""

    name: str = Field(..., min_length=2, max_length=255)
    email: EmailStr
    phone: str = Field(..., pattern=r"^\+?[0-9\s\-\(\)]+$")
    address: Optional[str] = None
    city: Optional[str] = None
    postal_code: Optional[str] = None
    country: str = "Sweden"
    description: Optional[str] = None
    website: Optional[str] = None


# Create Club schema
class ClubCreate(ClubBase):
    """Schema for creating a new club"""

    slug: str = Field(..., pattern=r"^[a-z0-9\-]+$")  # URL-friendly slug
    matchi_club_id: Optional[str] = None
    matchi_booking_url: Optional[str] = None

    membership_types: List[Dict[str, Any]] = Field(default_factory=list)
    pricing_info: Dict[str, Any] = Field(default_factory=dict)
    facilities: List[str] = Field(default_factory=list)
    opening_hours: Dict[str, Dict[str, str]] = Field(default_factory=dict)

    policies: Optional[str] = None
    custom_greeting: Optional[str] = None
    knowledge_base: Dict[str, Any] = Field(default_factory=dict)

    manager_name: Optional[str] = None
    manager_phone: Optional[str] = None
    manager_email: Optional[EmailStr] = None


# Update Club schema
class ClubUpdate(BaseModel):
    """Schema for updating an existing club (all fields optional)"""

    name: Optional[str] = Field(None, min_length=2, max_length=255)
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    address: Optional[str] = None
    city: Optional[str] = None
    postal_code: Optional[str] = None
    country: Optional[str] = None
    description: Optional[str] = None
    website: Optional[str] = None

    matchi_club_id: Optional[str] = None
    matchi_booking_url: Optional[str] = None

    membership_types: Optional[List[Dict[str, Any]]] = None
    pricing_info: Optional[Dict[str, Any]] = None
    facilities: Optional[List[str]] = None
    opening_hours: Optional[Dict[str, Dict[str, str]]] = None

    policies: Optional[str] = None
    custom_greeting: Optional[str] = None
    knowledge_base: Optional[Dict[str, Any]] = None

    is_active: Optional[bool] = None
    subscription_tier: Optional[str] = None

    manager_name: Optional[str] = None
    manager_phone: Optional[str] = None
    manager_email: Optional[EmailStr] = None

    vapi_phone_number: Optional[str] = None
    ai_assistant_id: Optional[str] = None


# Response Club schema
class ClubResponse(ClubBase):
    """Schema for Club responses"""

    id: UUID
    slug: str

    matchi_club_id: Optional[str] = None
    matchi_booking_url: Optional[str] = None

    membership_types: List[Dict[str, Any]]
    pricing_info: Dict[str, Any]
    facilities: List[str]
    opening_hours: Dict[str, Dict[str, str]]

    policies: Optional[str] = None
    custom_greeting: Optional[str] = None
    knowledge_base: Dict[str, Any]

    ai_assistant_id: Optional[str] = None
    vapi_phone_number: Optional[str] = None

    is_active: bool
    subscription_tier: str

    manager_name: Optional[str] = None
    manager_phone: Optional[str] = None
    manager_email: Optional[str] = None

    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True  # For SQLAlchemy compatibility


# List response
class ClubList(BaseModel):
    """Schema for list of clubs"""

    clubs: List[ClubResponse]
    total: int
    page: int = 1
    page_size: int = 50
