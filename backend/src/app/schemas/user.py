"""
User and Authentication Schemas
Pydantic models for request/response validation
"""

from __future__ import annotations

from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field, validator


# Authentication Schemas
class Token(BaseModel):
    """Response schema for login"""

    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    user: "UserResponse"


class TokenRefresh(BaseModel):
    """Request schema for token refresh"""

    refresh_token: str


class LoginRequest(BaseModel):
    """Request schema for login"""

    email: EmailStr
    password: str = Field(..., min_length=6)


class PasswordChange(BaseModel):
    """Request schema for password change"""

    old_password: str
    new_password: str = Field(..., min_length=8)

    @validator("new_password")
    def validate_password_strength(cls, v):
        """Ensure password has minimum strength"""
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters long")
        if not any(char.isdigit() for char in v):
            raise ValueError("Password must contain at least one digit")
        if not any(char.isupper() for char in v):
            raise ValueError("Password must contain at least one uppercase letter")
        return v


class PasswordReset(BaseModel):
    """Request schema for password reset"""

    email: EmailStr


# User Schemas
class UserBase(BaseModel):
    """Base user schema with common fields"""

    email: EmailStr
    username: str = Field(..., min_length=3, max_length=50)
    full_name: str = Field(..., min_length=1, max_length=255)
    phone: Optional[str] = None


class UserCreate(UserBase):
    """Schema for creating a new user"""

    password: str = Field(..., min_length=8)
    club_id: Optional[UUID] = None
    role: str = "club_staff"  # Default role

    @validator("password")
    def validate_password(cls, v):
        """Ensure password meets requirements"""
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters long")
        if not any(char.isdigit() for char in v):
            raise ValueError("Password must contain at least one digit")
        if not any(char.isupper() for char in v):
            raise ValueError("Password must contain at least one uppercase letter")
        return v


class UserUpdate(BaseModel):
    """Schema for updating user information"""

    email: Optional[EmailStr] = None
    username: Optional[str] = Field(None, min_length=3, max_length=50)
    full_name: Optional[str] = Field(None, min_length=1, max_length=255)
    phone: Optional[str] = None
    is_active: Optional[bool] = None
    is_verified: Optional[bool] = None
    role: Optional[str] = None


class UserResponse(BaseModel):
    """Schema for user response (without sensitive data)"""

    id: UUID
    club_id: Optional[UUID]
    email: str
    username: str
    full_name: str
    phone: Optional[str]
    role: str
    is_active: bool
    is_verified: bool
    last_login: Optional[datetime]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class UserDetailResponse(UserResponse):
    """Detailed user response with additional info"""

    failed_login_attempts: int
    locked_until: Optional[datetime]
    last_password_change: datetime

    class Config:
        from_attributes = True


# Update forward references
Token.model_rebuild()
