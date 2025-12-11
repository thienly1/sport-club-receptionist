"""
Customer Pydantic Schemas
Request and response models for Customer endpoints
"""

from datetime import datetime
from enum import Enum
from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field


# Enum for customer status
class CustomerStatus(str, Enum):
    LEAD = "lead"
    INTERESTED = "interested"
    TRIAL = "trial"
    MEMBER = "member"
    INACTIVE = "inactive"


# Base Customer schema
class CustomerBase(BaseModel):
    """Base Customer schema with common fields"""

    name: str = Field(..., min_length=2, max_length=255)
    phone: str = Field(..., pattern=r"^\+?[0-9\s\-\(\)]+$")
    email: Optional[EmailStr] = None


# Create Customer schema
class CustomerCreate(CustomerBase):
    """Schema for creating a new customer"""

    club_id: UUID
    source: Optional[str] = "phone_call"
    status: CustomerStatus = CustomerStatus.LEAD
    interested_in: Optional[str] = None
    membership_type_interest: Optional[str] = None
    preferred_contact_method: Optional[str] = "phone"
    notes: Optional[str] = None
    consent_marketing: bool = False


# Update Customer schema
class CustomerUpdate(BaseModel):
    """Schema for updating an existing customer"""

    name: Optional[str] = Field(None, min_length=2, max_length=255)
    phone: Optional[str] = None
    email: Optional[EmailStr] = None

    status: Optional[CustomerStatus] = None
    interested_in: Optional[str] = None
    membership_type_interest: Optional[str] = None
    preferred_contact_method: Optional[str] = None
    notes: Optional[str] = None

    requires_follow_up: Optional[bool] = None
    follow_up_date: Optional[datetime] = None
    is_high_priority: Optional[bool] = None

    converted_to_member: Optional[bool] = None
    conversion_date: Optional[datetime] = None

    consent_marketing: Optional[bool] = None


# Response Customer schema
class CustomerResponse(CustomerBase):
    """Schema for Customer responses"""

    id: UUID
    club_id: UUID

    source: Optional[str]
    status: CustomerStatus

    interested_in: Optional[str]
    membership_type_interest: Optional[str]
    preferred_contact_method: Optional[str]
    notes: Optional[str]

    requires_follow_up: bool
    follow_up_date: Optional[datetime]
    is_high_priority: bool

    converted_to_member: bool
    conversion_date: Optional[datetime]

    consent_marketing: bool

    first_contact_date: datetime
    last_contact_date: datetime
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# List response
class CustomerList(BaseModel):
    """Schema for list of customers"""

    customers: List[CustomerResponse]
    total: int
    page: int = 1
    page_size: int = 50


# Customer search/filter schema
class CustomerFilter(BaseModel):
    """Schema for filtering customers"""

    club_id: Optional[UUID] = None
    status: Optional[CustomerStatus] = None
    requires_follow_up: Optional[bool] = None
    is_high_priority: Optional[bool] = None
    converted_to_member: Optional[bool] = None
    search: Optional[str] = None  # Search in name, phone, email
