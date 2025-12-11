"""
Dashboard endpoints with real database statistics
"""

from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import and_, func, or_
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies.auth import get_current_active_user
from app.models.booking import Booking
from app.models.club import Club
from app.models.conversation import Conversation
from app.models.customer import Customer
from app.models.notification import Notification
from app.models.user import User, UserRole

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


@router.get("/club/{club_id}/stats")
async def get_club_stats(
    club_id: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """
    Get dashboard statistics for a specific club
    """
    # Verify user has access to this club (skip check for super_admin)
    if current_user.role != UserRole.SUPER_ADMIN:
        if current_user.club_id is None:
            raise HTTPException(status_code=403, detail="No club assigned to your account")
        if str(current_user.club_id) != str(club_id):
            raise HTTPException(
                status_code=403,
                detail=f"Access denied. Your club_id: {current_user.club_id}, Requested: {club_id}",
            )
    # For super_admin, check club exists
    if current_user.role == UserRole.SUPER_ADMIN:
        club = db.query(Club).filter(Club.id == club_id).first()
        if not club:
            raise HTTPException(status_code=404, detail=f"Club with ID {club_id} not found")

    # Calculate date ranges
    today = datetime.now().date()
    month_start = today.replace(day=1)

    # Total customers
    total_customers = db.query(Customer).filter(Customer.club_id == club_id).count()

    # New customers this month
    new_customers_this_month = (
        db.query(Customer)
        .filter(
            and_(
                Customer.club_id == club_id,
                func.date(Customer.created_at) >= month_start,
            )
        )
        .count()
    )

    # Total bookings
    total_bookings = db.query(Booking).filter(Booking.club_id == club_id).count()

    # Bookings today
    bookings_today = (
        db.query(Booking).filter(and_(Booking.club_id == club_id, func.date(Booking.booking_date) == today)).count()
    )

    # Bookings this month
    bookings_this_month = (
        db.query(Booking)
        .filter(
            and_(
                Booking.club_id == club_id,
                func.date(Booking.booking_date) >= month_start,
            )
        )
        .count()
    )

    # Revenue this month
    revenue_this_month_result = (
        db.query(func.coalesce(func.sum(Booking.price), 0))
        .filter(
            and_(
                Booking.club_id == club_id,
                func.date(Booking.booking_date) >= month_start,
                Booking.status.in_(["confirmed", "completed"]),
            )
        )
        .scalar()
    )
    revenue_this_month = float(revenue_this_month_result or 0)

    # Revenue today
    revenue_today_result = (
        db.query(func.coalesce(func.sum(Booking.price), 0))
        .filter(
            and_(
                Booking.club_id == club_id,
                func.date(Booking.booking_date) == today,
                Booking.status.in_(["confirmed", "completed"]),
            )
        )
        .scalar()
    )
    revenue_today = float(revenue_today_result or 0)

    # Active conversations
    active_conversations = (
        db.query(Conversation)
        .filter(
            and_(
                Conversation.club_id == club_id,
                Conversation.status.in_(["active", "completed"]),
            )
        )
        .count()
    )

    # Pending follow-ups
    pending_follow_ups = (
        db.query(Customer)
        .filter(
            and_(
                Customer.club_id == club_id,
                Customer.requires_follow_up.is_(True),
                or_(
                    Customer.follow_up_date.is_(None),
                    func.date(Customer.follow_up_date) <= today,
                ),
            )
        )
        .count()
    )

    # Unread notifications
    unread_notifications = (
        db.query(Notification).filter(and_(Notification.club_id == club_id, Notification.status == "pending")).count()
    )

    return {
        "total_customers": total_customers,
        "new_customers_this_month": new_customers_this_month,
        "total_bookings": total_bookings,
        "bookings_today": bookings_today,
        "bookings_this_month": bookings_this_month,
        "revenue_this_month": revenue_this_month,
        "revenue_today": revenue_today,
        "active_conversations": active_conversations,
        "pending_follow_ups": pending_follow_ups,
        "unread_notifications": unread_notifications,
    }


@router.get("/super-admin/stats")
async def get_super_admin_stats(current_user: User = Depends(get_current_active_user), db: Session = Depends(get_db)):
    """
    Get system-wide statistics (super_admin only)
    """
    # Verify user is super admin
    if current_user.role != UserRole.SUPER_ADMIN:
        raise HTTPException(
            status_code=403,
            detail="Only super admins can access system-wide statistics",
        )

    # Calculate date ranges
    today = datetime.now().date()
    month_start = today.replace(day=1)

    # Total clubs
    total_clubs = db.query(Club).count()

    # Active clubs
    active_clubs = (
        db.query(Club).filter(Club.is_active.is_(True)).count() if hasattr(Club, "is_active") else total_clubs
    )

    # Total users
    total_users = db.query(User).count()

    # Total customers across all clubs
    total_customers = db.query(Customer).count()

    # Total bookings this month across all clubs
    total_bookings_this_month = db.query(Booking).filter(func.date(Booking.booking_date) >= month_start).count()

    # Total revenue this month across all clubs
    total_revenue_result = (
        db.query(func.coalesce(func.sum(Booking.price), 0))
        .filter(
            and_(
                func.date(Booking.booking_date) >= month_start,
                Booking.status.in_(["confirmed", "completed"]),
            )
        )
        .scalar()
    )
    total_revenue_this_month = float(total_revenue_result or 0)

    return {
        "total_clubs": total_clubs,
        "active_clubs": active_clubs,
        "total_users": total_users,
        "total_customers": total_customers,
        "total_bookings_this_month": total_bookings_this_month,
        "total_revenue_this_month": total_revenue_this_month,
    }
