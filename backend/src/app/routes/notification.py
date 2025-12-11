"""
Notification API Routes
Endpoints for managing notifications (SMS, email, webhooks)
"""

from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies.auth import get_club_admin, get_current_active_user
from app.models.notification import Notification, NotificationStatus, NotificationType
from app.models.user import User
from app.schemas.notification import (
    NotificationCreate,
    NotificationList,
    NotificationResponse,
    NotificationUpdate,
)

router = APIRouter(prefix="/notifications", tags=["Notifications"])


@router.post("/", response_model=NotificationResponse, status_code=status.HTTP_201_CREATED)
async def create_notification(
    notification_data: NotificationCreate,
    current_user: User = Depends(get_club_admin),
    db: Session = Depends(get_db),
):
    """
    Create a new notification

    Requires club_admin or super_admin role
    """
    # Create notification
    notification = Notification(**notification_data.model_dump())
    db.add(notification)
    db.commit()
    db.refresh(notification)

    return notification


@router.get("/", response_model=NotificationList)
async def list_notifications(
    club_id: Optional[UUID] = None,
    notification_type: Optional[NotificationType] = None,
    status: Optional[NotificationStatus] = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """
    List notifications with filters

    Filters:
    - club_id: Filter by club
    - notification_type: Filter by type (escalation, booking_confirmation, etc.)
    - status: Filter by status (pending, sent, delivered, failed)
    """
    query = db.query(Notification)

    # Filter by club if user is not super admin
    if current_user.role != "super_admin":
        if current_user.club_id:
            query = query.filter(Notification.club_id == current_user.club_id)
    elif club_id:
        query = query.filter(Notification.club_id == club_id)

    if notification_type:
        query = query.filter(Notification.notification_type == notification_type)

    if status:
        query = query.filter(Notification.status == status)

    total = query.count()
    notifications = query.order_by(Notification.created_at.desc()).offset(skip).limit(limit).all()

    return {
        "notifications": notifications,
        "total": total,
        "page": (skip // limit) + 1,
        "page_size": limit,
    }


@router.get("/{notification_id}", response_model=NotificationResponse)
async def get_notification(
    notification_id: UUID,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Get a specific notification"""
    notification = db.query(Notification).filter(Notification.id == notification_id).first()

    if not notification:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Notification with ID {notification_id} not found",
        )

    # Check access
    if current_user.role != "super_admin" and notification.club_id != current_user.club_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")

    return notification


@router.patch("/{notification_id}", response_model=NotificationResponse)
async def update_notification(
    notification_id: UUID,
    notification_data: NotificationUpdate,
    current_user: User = Depends(get_club_admin),
    db: Session = Depends(get_db),
):
    """
    Update notification status or details

    Requires club_admin or super_admin role
    """
    notification = db.query(Notification).filter(Notification.id == notification_id).first()

    if not notification:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Notification with ID {notification_id} not found",
        )

    # Check access
    if current_user.role != "super_admin" and notification.club_id != current_user.club_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")

    # Update fields
    update_data = notification_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(notification, field, value)

    db.commit()
    db.refresh(notification)

    return notification


@router.delete("/{notification_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_notification(
    notification_id: UUID,
    current_user: User = Depends(get_club_admin),
    db: Session = Depends(get_db),
):
    """
    Delete a notification

    Requires club_admin or super_admin role
    """
    notification = db.query(Notification).filter(Notification.id == notification_id).first()

    if not notification:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Notification with ID {notification_id} not found",
        )

    # Check access
    if current_user.role != "super_admin" and notification.club_id != current_user.club_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")

    db.delete(notification)
    db.commit()

    return None


@router.get("/club/{club_id}/pending", response_model=NotificationList)
async def get_pending_notifications(
    club_id: UUID,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """
    Get all pending notifications for a club

    Useful for processing notification queues
    """
    # Check access
    if current_user.role != "super_admin" and club_id != current_user.club_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")

    notifications = (
        db.query(Notification)
        .filter(
            Notification.club_id == club_id,
            Notification.status == NotificationStatus.PENDING,
        )
        .order_by(Notification.created_at)
        .all()
    )

    return {
        "notifications": notifications,
        "total": len(notifications),
        "page": 1,
        "page_size": len(notifications),
    }


@router.post("/{notification_id}/retry", response_model=NotificationResponse)
async def retry_notification(
    notification_id: UUID,
    current_user: User = Depends(get_club_admin),
    db: Session = Depends(get_db),
):
    """
    Retry a failed notification

    Changes status back to pending for reprocessing
    Requires club_admin or super_admin role
    """
    notification = db.query(Notification).filter(Notification.id == notification_id).first()

    if not notification:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Notification with ID {notification_id} not found",
        )

    # Check access
    if current_user.role != "super_admin" and notification.club_id != current_user.club_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")

    # Only retry failed notifications
    if notification.status not in [
        NotificationStatus.FAILED,
        NotificationStatus.BOUNCED,
    ]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Can only retry failed or bounced notifications",
        )

    notification.status = NotificationStatus.PENDING
    notification.error_message = None
    notification.retry_count = (notification.retry_count or 0) + 1

    db.commit()
    db.refresh(notification)

    return notification


@router.get("/stats/{club_id}", response_model=dict)
async def get_notification_stats(
    club_id: UUID,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """
    Get notification statistics for a club

    Returns counts by status, type, and channel
    """
    # Check access
    if current_user.role != "super_admin" and club_id != current_user.club_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")

    # Count by status
    status_counts = (
        db.query(Notification.status, func.count(Notification.id))
        .filter(Notification.club_id == club_id)
        .group_by(Notification.status)
        .all()
    )

    # Count by type
    type_counts = (
        db.query(Notification.notification_type, func.count(Notification.id))
        .filter(Notification.club_id == club_id)
        .group_by(Notification.notification_type)
        .all()
    )

    # Count by channel
    channel_counts = (
        db.query(Notification.channel, func.count(Notification.id))
        .filter(Notification.club_id == club_id)
        .group_by(Notification.channel)
        .all()
    )

    return {
        "by_status": {status.value: count for status, count in status_counts},
        "by_type": {type_.value: count for type_, count in type_counts},
        "by_channel": {channel.value: count for channel, count in channel_counts},
        "total": db.query(Notification).filter(Notification.club_id == club_id).count(),
    }
