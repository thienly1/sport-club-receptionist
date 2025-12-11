"""
User Model
Represents admin/staff users who can access the system
"""

import enum
import uuid
from datetime import datetime

from sqlalchemy import Boolean, Column, DateTime
from sqlalchemy import Enum as SQLEnum
from sqlalchemy import ForeignKey, Integer, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.database import Base


class UserRole(str, enum.Enum):
    """User roles in the system"""

    SUPER_ADMIN = "super_admin"  # Full system access
    CLUB_ADMIN = "club_admin"  # Can manage their club
    CLUB_STAFF = "club_staff"  # Limited club access
    VIEWER = "viewer"  # Read-only access


class User(Base):
    """
    User Model
    Represents authenticated users (admins/staff) who can access the system
    """

    __tablename__ = "users"

    # Primary Key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Association (optional - super admins may not belong to a specific club)
    club_id = Column(UUID(as_uuid=True), ForeignKey("clubs.id"), nullable=True, index=True)

    # Authentication
    email = Column(String(255), unique=True, nullable=False, index=True)
    username = Column(String(100), unique=True, nullable=False, index=True)
    hashed_password = Column(String(255), nullable=False)

    # User Details
    full_name = Column(String(255), nullable=False)
    phone = Column(String(20))

    # Role & Permissions
    role = Column(
        SQLEnum(UserRole, values_callable=lambda x: [e.value for e in x]),
        default=UserRole.CLUB_STAFF,
        nullable=False,
        index=True,
    )
    is_active = Column(Boolean, default=True, nullable=False, index=True)
    is_verified = Column(Boolean, default=False, nullable=False)

    # Security
    last_login = Column(DateTime, nullable=True)
    last_password_change = Column(DateTime, default=datetime.utcnow)
    failed_login_attempts = Column(Integer, default=0)
    locked_until = Column(DateTime, nullable=True)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    club = relationship("Club", back_populates="users")

    def __repr__(self):
        return f"<User(username='{self.username}', email='{self.email}', role='{self.role}')>"

    @property
    def is_super_admin(self) -> bool:
        """Check if user is a super admin"""
        return self.role == UserRole.SUPER_ADMIN

    @property
    def is_club_admin(self) -> bool:
        """Check if user is a club admin"""
        return self.role == UserRole.CLUB_ADMIN

    @property
    def is_club_staff(self) -> bool:
        """Check if user is a club staff"""
        return self.role == UserRole.CLUB_STAFF

    @property
    def can_manage_club(self) -> bool:
        """Check if user can manage club settings"""
        return self.role in [UserRole.SUPER_ADMIN, UserRole.CLUB_ADMIN]
