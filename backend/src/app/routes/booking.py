"""
Booking API Routes
Endpoints for managing bookings
"""

import secrets
from datetime import datetime
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.booking import Booking
from app.models.booking import BookingStatus as BookingStatusEnum
from app.schemas.booking import (
    BookingCreate,
    BookingList,
    BookingResponse,
    BookingStatus,
    BookingUpdate,
)
from app.services.notification_service import NotificationService

router = APIRouter(prefix="/bookings", tags=["Bookings"])


def check_double_booking(
    db: Session,
    club_id: UUID,
    resource_name: str,
    start_time: datetime,
    end_time: datetime,
    exclude_booking_id: Optional[UUID] = None,
) -> bool:
    """
    Check if there's already a booking for the same resource at the same time.
    Returns True if there's a conflict (double booking), False if available.
    """
    # Only check active bookings (not cancelled or no-show)
    active_statuses = [BookingStatusEnum.PENDING, BookingStatusEnum.CONFIRMED]

    # Query for overlapping bookings
    query = db.query(Booking).filter(
        Booking.club_id == club_id,
        Booking.resource_name == resource_name,
        Booking.status.in_(active_statuses),
        # Check for time overlap
        Booking.start_time < end_time,
        Booking.end_time > start_time,
    )

    if exclude_booking_id:
        query = query.filter(Booking.id != exclude_booking_id)

    existing_booking = query.first()

    # Return True if there's a conflict
    return existing_booking is not None


@router.post("/", response_model=BookingResponse, status_code=status.HTTP_201_CREATED)
async def create_booking(
    booking_data: BookingCreate,
    send_confirmation: bool = Query(True, description="Send SMS confirmation"),
    db: Session = Depends(get_db),
):
    """Create a new booking"""
    # Check for double booking
    if check_double_booking(
        db=db,
        club_id=booking_data.club_id,
        resource_name=booking_data.resource_name,
        start_time=booking_data.start_time,
        end_time=booking_data.end_time,
    ):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"'{booking_data.resource_name}' is already booked for the requested time slot",
        )

    # Generate confirmation code
    confirmation_code = secrets.token_hex(4).upper()

    # Create booking
    booking = Booking(**booking_data.model_dump(), confirmation_code=confirmation_code)

    db.add(booking)
    db.commit()
    db.refresh(booking)

    # Send confirmation SMS
    if send_confirmation and booking.status == BookingStatusEnum.CONFIRMED:
        notification_service = NotificationService()
        await notification_service.send_booking_confirmation(db=db, booking_id=booking.id)
        booking.confirmation_sent_at = datetime.utcnow()
        db.commit()
        db.refresh(booking)

    return booking


@router.get("/", response_model=BookingList)
def list_bookings(
    club_id: Optional[UUID] = None,
    customer_id: Optional[UUID] = None,
    status: Optional[BookingStatus] = None,
    from_date: Optional[datetime] = None,
    to_date: Optional[datetime] = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db),
):
    """List bookings with filters"""
    query = db.query(Booking)

    if club_id:
        query = query.filter(Booking.club_id == club_id)

    if customer_id:
        query = query.filter(Booking.customer_id == customer_id)

    if status:
        query = query.filter(Booking.status == status)

    if from_date:
        query = query.filter(Booking.booking_date >= from_date)

    if to_date:
        query = query.filter(Booking.booking_date <= to_date)

    total = query.count()
    bookings = query.order_by(Booking.booking_date.desc()).offset(skip).limit(limit).all()

    return {
        "bookings": bookings,
        "total": total,
        "page": (skip // limit) + 1,
        "page_size": limit,
    }


@router.get("/{booking_id}", response_model=BookingResponse)
def get_booking(booking_id: UUID, db: Session = Depends(get_db)):
    """Get a specific booking"""
    booking = db.query(Booking).filter(Booking.id == booking_id).first()

    if not booking:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Booking with ID {booking_id} not found",
        )

    return booking


@router.patch("/{booking_id}", response_model=BookingResponse)
def update_booking(booking_id: UUID, booking_data: BookingUpdate, db: Session = Depends(get_db)):
    """Update booking information"""
    booking = db.query(Booking).filter(Booking.id == booking_id).first()

    if not booking:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Booking with ID {booking_id} not found",
        )

    # If updating resource or time, check for double booking
    update_data = booking_data.model_dump(exclude_unset=True)

    # Check if we're changing resource or time
    if any(field in update_data for field in ["resource_name", "start_time", "end_time"]):
        new_resource = update_data.get("resource_name", booking.resource_name)
        new_start = update_data.get("start_time", booking.start_time)
        new_end = update_data.get("end_time", booking.end_time)

        # Check for double booking (exclude current booking)
        if check_double_booking(
            db=db,
            club_id=booking.club_id,
            resource_name=new_resource,
            start_time=new_start,
            end_time=new_end,
            exclude_booking_id=booking_id,
        ):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"'{new_resource}' is already booked for the requested time slot",
            )

    # Update fields
    for field, value in update_data.items():
        setattr(booking, field, value)

    db.commit()
    db.refresh(booking)

    return booking


@router.post("/{booking_id}/confirm")
async def confirm_booking(booking_id: UUID, send_sms: bool = Query(True), db: Session = Depends(get_db)):
    """Confirm a pending booking"""
    booking = db.query(Booking).filter(Booking.id == booking_id).first()

    if not booking:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Booking with ID {booking_id} not found",
        )

    booking.status = BookingStatusEnum.CONFIRMED
    db.commit()
    db.refresh(booking)

    # Send confirmation SMS
    if send_sms:
        notification_service = NotificationService()
        await notification_service.send_booking_confirmation(db=db, booking_id=booking.id)
        booking.confirmation_sent_at = datetime.utcnow()
        db.commit()

    return {"message": "Booking confirmed", "booking": booking}


@router.post("/{booking_id}/cancel")
def cancel_booking(booking_id: UUID, reason: Optional[str] = None, db: Session = Depends(get_db)):
    """Cancel a booking"""
    booking = db.query(Booking).filter(Booking.id == booking_id).first()

    if not booking:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Booking with ID {booking_id} not found",
        )

    booking.status = BookingStatusEnum.CANCELLED
    booking.cancellation_reason = reason
    booking.cancelled_at = datetime.utcnow()
    booking.cancelled_by = "system"

    db.commit()
    db.refresh(booking)

    return {"message": "Booking cancelled", "booking": booking}


# New endpoint to check availability
@router.get("/check-availability/")
def check_availability(
    club_id: UUID = Query(..., description="Club ID"),
    resource_name: str = Query(..., description="Resource name (e.g., 'Court 1')"),
    start_time: datetime = Query(..., description="Start time of the booking"),
    end_time: datetime = Query(..., description="End time of the booking"),
    db: Session = Depends(get_db),
):
    """Check if a resource is available for booking"""
    has_conflict = check_double_booking(
        db=db,
        club_id=club_id,
        resource_name=resource_name,
        start_time=start_time,
        end_time=end_time,
    )

    return {
        "available": not has_conflict,
        "club_id": club_id,
        "resource_name": resource_name,
        "start_time": start_time,
        "end_time": end_time,
        "message": ("Resource is available" if not has_conflict else "Resource is already booked"),
    }
