"""
Notification Service
Handles SMS, email, and other notifications via Twilio
"""

import logging
from datetime import datetime
from typing import Any, Dict, Optional
from uuid import UUID

from sqlalchemy.orm import Session
from twilio.rest import Client

from app.config import settings
from app.models.booking import Booking
from app.models.club import Club
from app.models.customer import Customer
from app.models.notification import (
    Notification,
    NotificationChannel,
    NotificationStatus,
    NotificationType,
)

logger = logging.getLogger(__name__)


class NotificationService:
    """Service for sending notifications (SMS, email, etc.)"""

    def __init__(self):
        self.twilio_client = Client(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)
        self.from_number = settings.TWILIO_PHONE_NUMBER

    def send_sms(self, to_phone: str, message: str, priority: str = "normal") -> Dict[str, Any]:
        """
        Send SMS via Twilio

        Args:
            to_phone: Recipient phone number
            message: Message content
            priority: Priority level

        Returns:
            Result dictionary with status
        """
        try:
            twilio_message = self.twilio_client.messages.create(body=message, from_=self.from_number, to=to_phone)

            return {
                "success": True,
                "message_id": twilio_message.sid,
                "status": twilio_message.status,
                "to": to_phone,
                "sent_at": datetime.utcnow(),
            }

        except Exception as e:
            logger.error(f"Failed to send SMS to {to_phone}: {str(e)}")
            return {"success": False, "error": str(e), "to": to_phone}

    def send_escalation_to_manager(
        self,
        db: Session,
        club_id: UUID,
        customer_name: str,
        customer_phone: str,
        question: str,
        conversation_id: Optional[UUID] = None,
    ) -> Dict[str, Any]:
        """
        Send escalation notification to club manager

        Args:
            db: Database session
            club_id: Club UUID
            customer_name: Customer's name
            customer_phone: Customer's phone
            question: Question that couldn't be answered
            conversation_id: Optional conversation ID

        Returns:
            Result dictionary
        """
        club = db.query(Club).filter(Club.id == club_id).first()
        if not club or not club.manager_phone:
            return {"success": False, "error": "No manager phone number configured"}

        message = f"""
        🔔 ESCALATION - {club.name}

        Customer: {customer_name}
        Phone: {customer_phone}

        Question: {question}

        Please follow up with this customer.
        """.strip()

        # Send SMS
        result = self.send_sms(club.manager_phone, message, priority="high")

        # Log notification in database
        notification = Notification(
            club_id=club_id,
            conversation_id=conversation_id,
            notification_type=NotificationType.ESCALATION,
            channel=NotificationChannel.SMS,
            status=(NotificationStatus.SENT if result.get("success") else NotificationStatus.FAILED),
            recipient_name=club.manager_name,
            recipient_phone=club.manager_phone,
            message=message,
            provider="twilio",
            provider_message_id=result.get("message_id"),
            sent_at=datetime.utcnow() if result.get("success") else None,
            error_message=result.get("error"),
            priority="high",
        )
        db.add(notification)
        db.commit()

        return result

    def send_booking_confirmation(self, db: Session, booking_id: UUID) -> Dict[str, Any]:
        """
        Send booking confirmation SMS

        Args:
            db: Database session
            booking_id: Booking UUID

        Returns:
            Result dictionary
        """
        booking = db.query(Booking).filter(Booking.id == booking_id).first()
        if not booking:
            return {"success": False, "error": "Booking not found"}

        club = db.query(Club).filter(Club.id == booking.club_id).first()

        message = f"""
        ✅ Booking Confirmed - {club.name}

        Date: {booking.booking_date.strftime('%Y-%m-%d')}
        Time: {booking.start_time.strftime('%H:%M')} - {booking.end_time.strftime('%H:%M')}
        Resource: {booking.resource_name}
        Confirmation: {booking.confirmation_code}

        Thank you for booking with us!
        """.strip()

        result = self.send_sms(booking.contact_phone, message)

        # Log notification
        notification = Notification(
            club_id=booking.club_id,
            customer_id=booking.customer_id,
            booking_id=booking_id,
            conversation_id=booking.conversation_id,
            notification_type=NotificationType.BOOKING_CONFIRMATION,
            channel=NotificationChannel.SMS,
            status=(NotificationStatus.SENT if result.get("success") else NotificationStatus.FAILED),
            recipient_name=booking.contact_name,
            recipient_phone=booking.contact_phone,
            message=message,
            provider="twilio",
            provider_message_id=result.get("message_id"),
            sent_at=datetime.utcnow() if result.get("success") else None,
            error_message=result.get("error"),
        )
        db.add(notification)
        db.commit()

        return result

    def send_lead_alert(self, db: Session, club_id: UUID, customer_id: UUID) -> Dict[str, Any]:
        """
        Send new lead alert to manager

        Args:
            db: Database session
            club_id: Club UUID
            customer_id: Customer UUID

        Returns:
            Result dictionary
        """
        club = db.query(Club).filter(Club.id == club_id).first()
        customer = db.query(Customer).filter(Customer.id == customer_id).first()

        if not club or not customer or not club.manager_phone:
            return {"success": False, "error": "Missing data"}

        message = f"""
        🎯 NEW LEAD - {club.name}

        Name: {customer.name}
        Phone: {customer.phone}
        Email: {customer.email or 'N/A'}
        Interest: {customer.interested_in or 'General inquiry'}
        Status: {customer.status}

        Consider following up!
        """.strip()

        result = self.send_sms(club.manager_phone, message)

        # Log notification
        notification = Notification(
            club_id=club_id,
            customer_id=customer_id,
            notification_type=NotificationType.LEAD_ALERT,
            channel=NotificationChannel.SMS,
            status=(NotificationStatus.SENT if result.get("success") else NotificationStatus.FAILED),
            recipient_name=club.manager_name,
            recipient_phone=club.manager_phone,
            message=message,
            provider="twilio",
            provider_message_id=result.get("message_id"),
            sent_at=datetime.utcnow() if result.get("success") else None,
            error_message=result.get("error"),
        )
        db.add(notification)
        db.commit()

        return result

    def send_booking_reminder(self, db: Session, booking_id: UUID, hours_before: int = 24) -> Dict[str, Any]:
        """
        Send booking reminder SMS

        Args:
            db: Database session
            booking_id: Booking UUID
            hours_before: Hours before booking

        Returns:
            Result dictionary
        """
        booking = db.query(Booking).filter(Booking.id == booking_id).first()
        if not booking:
            return {"success": False, "error": "Booking not found"}

        club = db.query(Club).filter(Club.id == booking.club_id).first()

        message = f"""
        ⏰ Booking Reminder - {club.name}

        Your booking is in {hours_before} hours!

        Date: {booking.booking_date.strftime('%Y-%m-%d')}
        Time: {booking.start_time.strftime('%H:%M')}
        Resource: {booking.resource_name}

        See you soon!
        """.strip()

        result = self.send_sms(booking.contact_phone, message)

        # Log notification
        notification = Notification(
            club_id=booking.club_id,
            customer_id=booking.customer_id,
            booking_id=booking_id,
            notification_type=NotificationType.BOOKING_REMINDER,
            channel=NotificationChannel.SMS,
            status=(NotificationStatus.SENT if result.get("success") else NotificationStatus.FAILED),
            recipient_name=booking.contact_name,
            recipient_phone=booking.contact_phone,
            message=message,
            provider="twilio",
            provider_message_id=result.get("message_id"),
            sent_at=datetime.utcnow() if result.get("success") else None,
            error_message=result.get("error"),
        )
        db.add(notification)
        db.commit()

        return result
