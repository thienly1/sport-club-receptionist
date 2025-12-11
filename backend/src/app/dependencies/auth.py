"""
Authentication Dependencies
FastAPI dependencies for protecting routes and getting current user
"""

from datetime import datetime
from typing import Optional

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.user import User, UserRole
from app.utils.auth import decode_access_token

# Security scheme
security = HTTPBearer(auto_error=False)


async def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    db: Session = Depends(get_db),
) -> User:
    """
    Get the current authenticated user from JWT token

    Args:
        credentials: Bearer token from request header
        db: Database session

    Returns:
        User: Current authenticated user

    Raises:
        HTTPException: If authentication fails
    """
    # Check if credentials is None (no token provided)
    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token = credentials.credentials

    try:
        user_id = decode_access_token(token)
    except HTTPException:
        # Re-raise the 401 from decode_access_token
        raise

    # Get user from database
    user = db.query(User).filter(User.id == user_id).first()

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Inactive user account",
        )

    # Check if account is locked
    if user.locked_until and user.locked_until > datetime.utcnow():
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is temporarily locked due to multiple failed login attempts",
        )

    return user


async def get_current_active_user(
    current_user: User = Depends(get_current_user),
) -> User:
    """
    Ensure user is active

    Args:
        current_user: Current user from get_current_user

    Returns:
        User: Active user

    Raises:
        HTTPException: If user is inactive
    """
    if not current_user.is_active:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Inactive user")
    return current_user


async def get_current_verified_user(
    current_user: User = Depends(get_current_active_user),
) -> User:
    """
    Ensure user is verified

    Args:
        current_user: Current user from get_current_active_user

    Returns:
        User: Verified user

    Raises:
        HTTPException: If user is not verified
    """
    if not current_user.is_verified:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Please verify your email address",
        )
    return current_user


def require_role(*allowed_roles: UserRole):
    """
    Dependency factory to check if user has required role

    Usage:
        @app.get("/admin", dependencies=[Depends(require_role(UserRole.SUPER_ADMIN))])

    Args:
        allowed_roles: Roles that are allowed to access the endpoint

    Returns:
        Dependency function
    """

    async def role_checker(
        current_user: User = Depends(get_current_active_user),
    ) -> User:
        if current_user.role not in allowed_roles:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient permissions")
        return current_user

    return role_checker


async def get_super_admin(
    current_user: User = Depends(require_role(UserRole.SUPER_ADMIN)),
) -> User:
    """Get current user and ensure they are a super admin"""
    return current_user


async def get_club_admin(
    current_user: User = Depends(require_role(UserRole.CLUB_ADMIN)),
) -> User:
    """Get current user and ensure they are at least a club admin"""
    return current_user


async def get_club_staff(
    current_user: User = Depends(require_role(UserRole.CLUB_STAFF)),
) -> User:
    """Get current user and ensure they are at least a club admin"""
    return current_user


def verify_club_access(user: User, club_id: str) -> None:
    """
    Verify that a user has access to a specific club

    Super admins have access to all clubs
    Other users can only access their own club

    Args:
        user: Current user
        club_id: Club ID to check access for

    Raises:
        HTTPException: If user doesn't have access to the club
    """
    if user.role == UserRole.SUPER_ADMIN:
        return  # Super admin has access to all clubs

    if user.club_id is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User is not associated with any club",
        )

    if str(user.club_id) != str(club_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied: You can only access your own club's data",
        )


def get_accessible_club_id(user: User, requested_club_id: Optional[str] = None) -> Optional[str]:
    """
    Get the club ID that a user can access

    If user is super_admin and no club_id is requested, returns None (access all)
    If user is super_admin and club_id is requested, returns that club_id
    If user is staff/admin, returns their club_id (ignores requested_club_id)

    Args:
        user: Current user
        requested_club_id: Optional club ID from request

    Returns:
        Club ID to filter by, or None to access all
    """
    if user.role == UserRole.SUPER_ADMIN:
        return requested_club_id  # Can access requested club or all

    # Staff and admins can only access their own club
    return str(user.club_id) if user.club_id else None


async def verify_resource_access(user: User, resource_club_id: str, resource_name: str = "resource") -> None:
    """
    Verify that a user can access a resource belonging to a club

    Args:
        user: Current user
        resource_club_id: Club ID that owns the resource
        resource_name: Name of resource (for error message)

    Raises:
        HTTPException: If user doesn't have access
    """
    if user.role != UserRole.SUPER_ADMIN:
        if user.club_id is None or str(user.club_id) != str(resource_club_id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access denied: This {resource_name} belongs to another club",
            )
