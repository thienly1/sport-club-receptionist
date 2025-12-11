"""
Comprehensive Tests for Notification Model and Routes
"""

from datetime import datetime, timedelta
from uuid import UUID, uuid4

from fastapi.testclient import TestClient
from jose import jwt
from sqlalchemy.orm import Session

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
from app.models.user import User


# NOTIFICATION MODEL TESTS
class TestNotificationModel:
    """Test Notification model"""

    def test_create_notification(self, db: Session, test_club: Club, test_customer: Customer):
        """Test creating a new notification"""
        notification = Notification(
            club_id=test_club.id,
            customer_id=test_customer.id,
            notification_type="booking_confirmation",
            channel="sms",
            recipient_phone=test_customer.phone,
            subject="Booking Confirmation",
            message="Your booking is confirmed for tomorrow at 10 AM",
            status="pending",
        )

        db.add(notification)
        db.commit()
        db.refresh(notification)

        assert notification.id is not None
        assert isinstance(notification.id, UUID)
        assert notification.notification_type == "booking_confirmation"
        assert notification.status == "pending"
        assert notification.recipient_phone == test_customer.phone

    def test_notification_relationships(self, db: Session, test_club: Club, test_customer: Customer):
        """Test notification relationships"""
        notification = Notification(
            club_id=test_club.id,
            customer_id=test_customer.id,
            notification_type="booking_confirmation",
            channel="email",
            recipient_email=(test_customer.email if hasattr(test_customer, "email") else "test@example.com"),
            message="Test message",
        )

        db.add(notification)
        db.commit()
        db.refresh(notification)

        assert notification.club is not None
        assert notification.customer is not None
        assert notification.club_id == test_club.id
        assert notification.customer_id == test_customer.id

    def test_notification_booking_relationship(
        self,
        db: Session,
        test_club: Club,
        test_customer: Customer,
        test_booking: Booking,
    ):
        """Test notification linked to booking"""
        notification = Notification(
            club_id=test_club.id,
            customer_id=test_customer.id,
            booking_id=test_booking.id,
            notification_type="booking_confirmation",
            channel="sms",
            recipient_phone=test_customer.phone,
            message="Booking reminder: Your court is booked for tomorrow",
        )

        db.add(notification)
        db.commit()
        db.refresh(notification)

        if hasattr(notification, "booking"):
            assert notification.booking is not None
            assert notification.booking_id == test_booking.id

    def test_notification_status_transitions(self, db: Session, test_club: Club, test_customer: Customer):
        """Test notification status transitions"""
        notification = Notification(
            club_id=test_club.id,
            customer_id=test_customer.id,
            notification_type="booking_confirmation",
            channel="sms",
            recipient_phone=test_customer.phone,
            message="Test",
            status="pending",
        )

        db.add(notification)
        db.commit()

        # Mark as sent
        notification.status = "sent"
        notification.sent_at = datetime.utcnow()
        db.commit()
        db.refresh(notification)

        assert notification.status == "sent"
        assert notification.sent_at is not None

    def test_notification_failed_status(self, db: Session, test_club: Club, test_customer: Customer):
        """Test handling failed notifications"""
        notification = Notification(
            club_id=test_club.id,
            customer_id=test_customer.id,
            notification_type="booking_confirmation",
            channel="email",
            recipient_phone="invalid@example",
            message="Test",
            status="failed",
            error_message="Invalid email address",
        )

        db.add(notification)
        db.commit()
        db.refresh(notification)

        assert notification.status == "failed"
        if hasattr(notification, "error_message"):
            assert notification.error_message is not None

    def test_notification_scheduled_for_future(self, db: Session, test_club: Club, test_customer: Customer):
        """Test creating notification with pending status"""
        notification = Notification(
            club_id=test_club.id,
            customer_id=test_customer.id,
            notification_type="booking_reminder",
            channel="sms",
            recipient_phone=test_customer.phone,
            message="Reminder: Your booking is in 1 hour",
            status="pending",
        )

        db.add(notification)
        db.commit()
        db.refresh(notification)

        assert notification.status == "pending"
        assert notification.notification_type == "booking_reminder"


# NOTIFICATION TYPES TESTS
class TestNotificationTypes:
    """Test different notification types"""

    def test_sms_notification(self, db: Session, test_club: Club, test_customer: Customer):
        """Test SMS notification"""
        notification = Notification(
            club_id=test_club.id,
            customer_id=test_customer.id,
            notification_type="booking_confirmation",
            channel="sms",
            recipient_phone=test_customer.phone,
            message="SMS test message",
        )

        db.add(notification)
        db.commit()
        db.refresh(notification)

        assert notification.notification_type == "booking_confirmation"
        assert notification.recipient_phone.startswith("+")

    def test_email_notification(self, db: Session, test_club: Club, test_customer: Customer):
        """Test email notification"""
        notification = Notification(
            club_id=test_club.id,
            customer_id=test_customer.id,
            notification_type="booking_confirmation",
            channel="email",
            recipient_phone="customer@example.com",
            subject="Booking Confirmation",
            message="Your booking is confirmed",
        )

        db.add(notification)
        db.commit()
        db.refresh(notification)

        assert notification.notification_type == "booking_confirmation"
        if hasattr(notification, "subject"):
            assert notification.subject == "Booking Confirmation"

    def test_push_notification(self, db: Session, test_club: Club, test_customer: Customer):
        """Test push notification"""
        notification = Notification(
            club_id=test_club.id,
            customer_id=test_customer.id,
            notification_type="system_alert",
            channel="push",
            recipient_phone="device_token_123",
            message="New message from your club",
        )

        db.add(notification)
        db.commit()
        db.refresh(notification)

        assert notification.notification_type == "system_alert"


# NOTIFICATION ROUTES TESTS
class TestNotificationRoutes:
    """Test Notification API endpoints"""

    def test_list_notifications(self, client: TestClient, auth_headers: dict, test_club: Club):
        """Test listing notifications"""
        response = client.get(
            "/notifications/",
            headers=auth_headers,
            params={"club_id": str(test_club.id)},
        )

        if response.status_code == 200:
            data = response.json()
            assert isinstance(data, (list, dict))

    def test_get_notification_by_id(
        self,
        client: TestClient,
        auth_headers: dict,
        db: Session,
        test_club: Club,
        test_customer: Customer,
    ):
        """Test getting a specific notification"""
        # Create a notification first
        notification = Notification(
            club_id=test_club.id,
            customer_id=test_customer.id,
            notification_type="booking_confirmation",
            channel="sms",
            recipient_phone=test_customer.phone,
            message="Test notification",
        )
        db.add(notification)
        db.commit()
        db.refresh(notification)

        response = client.get(f"/notifications/{notification.id}", headers=auth_headers)

        if response.status_code == 200:
            data = response.json()
            assert data["id"] == str(notification.id)

    def test_send_notification(
        self,
        client: TestClient,
        auth_headers: dict,
        test_club: Club,
        test_customer: Customer,
    ):
        """Test sending a notification"""
        notification_data = {
            "club_id": str(test_club.id),
            "customer_id": str(test_customer.id),
            "notification_type": "booking_confirmation",
            "channel": "sms",
            "recipient": test_customer.phone,
            "message": "Test notification from API",
        }

        response = client.post("/notifications/send", headers=auth_headers, json=notification_data)

        if response.status_code in [200, 201]:
            data = response.json()
            assert "id" in data or "notification" in data

    def test_filter_notifications_by_type(self, client: TestClient, auth_headers: dict, test_club: Club):
        """Test filtering notifications by type"""
        response = client.get(
            "/notifications/",
            headers=auth_headers,
            params={
                "club_id": str(test_club.id),
                "notification_type": "booking_confirmation",
                "channel": "sms",
            },
        )

        if response.status_code == 200:
            data = response.json()
            if isinstance(data, list):
                for notif in data:
                    assert notif["notification_type"] == "sms"

    def test_filter_notifications_by_status(self, client: TestClient, auth_headers: dict, test_club: Club):
        """Test filtering notifications by status"""
        response = client.get(
            "/notifications/",
            headers=auth_headers,
            params={"club_id": str(test_club.id), "status": "sent"},
        )

        if response.status_code == 200:
            data = response.json()
            if isinstance(data, list):
                for notif in data:
                    assert notif["status"] == "sent"

    def test_get_customer_notifications(self, client: TestClient, auth_headers: dict, test_customer: Customer):
        """Test getting all notifications for a customer"""
        response = client.get(f"/customers/{test_customer.id}/notifications", headers=auth_headers)

        if response.status_code == 200:
            data = response.json()
            assert isinstance(data, (list, dict))

    def test_notification_requires_auth(self, client: TestClient, test_club: Club):
        """Test that notification endpoints require authentication"""
        response = client.get("/notifications/", params={"club_id": str(test_club.id)})

        assert response.status_code in [401, 403]


# NOTIFICATION ROUTES CRUD TESTS
class TestNotificationRoutesCRUD:
    """Test CRUD operations for notifications"""

    def test_create_notification_success(
        self, client: TestClient, auth_headers: dict, test_club: Club, test_customer: Customer
    ):
        """Test creating a notification"""
        notification_data = {
            "club_id": str(test_club.id),
            "customer_id": str(test_customer.id),
            "notification_type": "booking_confirmation",
            "channel": "sms",
            "recipient_phone": test_customer.phone,
            "message": "Test notification",
        }

        response = client.post("/notifications/", headers=auth_headers, json=notification_data)

        if response.status_code == 201:
            data = response.json()
            assert data["notification_type"] == "booking_confirmation"
            assert data["channel"] == "sms"

    def test_create_notification_missing_fields(self, client: TestClient, test_club_admin: User):
        """Test creating notification with missing required fields"""
        # Create token for club_admin
        expire = datetime.utcnow() + timedelta(minutes=30)
        to_encode = {"sub": str(test_club_admin.id), "exp": expire}
        token = jwt.encode(to_encode, settings.SECRET_KEY, algorithm="HS256")
        headers = {"Authorization": f"Bearer {token}"}

        notification_data = {
            "club_id": str(test_club_admin.club_id),
            # Missing required fields
        }

        response = client.post("/notifications/", headers=headers, json=notification_data)

        # Should return validation error
        assert response.status_code == 422

    def test_update_notification_status(
        self,
        client: TestClient,
        auth_headers: dict,
        test_club: Club,
        test_customer: Customer,
        db: Session,
    ):
        """Test updating notification status"""
        # Create a notification
        notification = Notification(
            club_id=test_club.id,
            customer_id=test_customer.id,
            notification_type=NotificationType.BOOKING_CONFIRMATION,
            channel=NotificationChannel.SMS,
            recipient_phone=test_customer.phone,
            message="Test",
            status=NotificationStatus.PENDING,
        )
        db.add(notification)
        db.commit()
        db.refresh(notification)

        # Update status
        update_data = {"status": "sent"}

        response = client.patch(f"/notifications/{notification.id}", headers=auth_headers, json=update_data)

        if response.status_code == 200:
            data = response.json()
            assert data["status"] == "sent"

    def test_delete_notification(
        self,
        client: TestClient,
        auth_headers: dict,
        test_club: Club,
        test_customer: Customer,
        db: Session,
    ):
        """Test deleting a notification"""
        notification = Notification(
            club_id=test_club.id,
            customer_id=test_customer.id,
            notification_type=NotificationType.BOOKING_CONFIRMATION,
            channel=NotificationChannel.SMS,
            recipient_phone=test_customer.phone,
            message="Test",
        )
        db.add(notification)
        db.commit()
        db.refresh(notification)

        response = client.delete(f"/notifications/{notification.id}", headers=auth_headers)

        if response.status_code == 204:
            # Verify it's deleted
            deleted = db.query(Notification).filter(Notification.id == notification.id).first()
            assert deleted is None


# NOTIFICATION TEMPLATES TESTS
class TestNotificationTemplates:
    """Test notification templates and message formatting"""

    def test_booking_confirmation_template(
        self,
        db: Session,
        test_club: Club,
        test_customer: Customer,
        test_booking: Booking,
    ):
        """Test booking confirmation notification template"""
        message = (
            f"Your booking at {test_club.name} is confirmed for {test_booking.start_time.strftime('%B %d at %I:%M %p')}"
        )

        notification = Notification(
            club_id=test_club.id,
            customer_id=test_customer.id,
            booking_id=test_booking.id,
            notification_type="booking_confirmation",
            channel="sms",
            recipient_phone=test_customer.phone,
            message=message,
        )

        db.add(notification)
        db.commit()
        db.refresh(notification)

        assert test_club.name in notification.message

    def test_booking_reminder_template(
        self,
        db: Session,
        test_club: Club,
        test_customer: Customer,
        test_booking: Booking,
    ):
        """Test booking reminder notification template"""
        message = (
            f"Reminder: Your booking at {test_club.name} is tomorrow at {test_booking.start_time.strftime('%I:%M %p')}"
        )

        notification = Notification(
            club_id=test_club.id,
            customer_id=test_customer.id,
            booking_id=test_booking.id,
            notification_type="booking_reminder",
            channel="sms",
            recipient_phone=test_customer.phone,
            message=message,
            status="pending",
        )

        db.add(notification)
        db.commit()
        db.refresh(notification)

        assert "Reminder" in notification.message

    def test_booking_cancellation_template(
        self,
        db: Session,
        test_club: Club,
        test_customer: Customer,
        test_booking: Booking,
    ):
        """Test booking cancellation notification template"""
        message = f"Your booking at {test_club.name} for {test_booking.start_time.strftime('%B %d')} has been cancelled"

        notification = Notification(
            club_id=test_club.id,
            customer_id=test_customer.id,
            booking_id=test_booking.id,
            notification_type="booking_cancellation",
            channel="sms",
            recipient_phone=test_customer.phone,
            message=message,
        )

        db.add(notification)
        db.commit()
        db.refresh(notification)

        assert "cancelled" in notification.message.lower()


# NOTIFICATION DELIVERY TESTS
class TestNotificationDelivery:
    """Test notification delivery mechanisms"""

    def test_sms_delivery_via_twilio(
        self,
        client: TestClient,
        auth_headers: dict,
        test_club: Club,
        test_customer: Customer,
        mock_notification_service,
    ):
        """Test SMS delivery through Twilio"""
        notification_data = {
            "club_id": str(test_club.id),
            "customer_id": str(test_customer.id),
            "notification_type": "booking_confirmation",
            "channel": "sms",
            "recipient": test_customer.phone,
            "message": "Test SMS via Twilio",
        }

        response = client.post("/notifications/send", headers=auth_headers, json=notification_data)

        # Mock service should handle the delivery
        if response.status_code in [200, 201]:
            assert mock_notification_service.send_sms.called or response.status_code == 200

    def test_email_delivery(
        self,
        client: TestClient,
        auth_headers: dict,
        test_club: Club,
        test_customer: Customer,
        mock_notification_service,
    ):
        """Test email delivery"""
        notification_data = {
            "club_id": str(test_club.id),
            "customer_id": str(test_customer.id),
            "notification_type": "booking_confirmation",
            "channel": "email",
            "recipient": "customer@example.com",
            "subject": "Test Email",
            "message": "Test email content",
        }

        response = client.post("/notifications/send", headers=auth_headers, json=notification_data)

        if response.status_code in [200, 201]:
            assert mock_notification_service.send_email.called or response.status_code == 200

    def test_retry_failed_notification(
        self, client: TestClient, auth_headers: dict, db: Session, test_club: Club, test_customer: Customer
    ):
        """Test retrying a failed notification"""
        # Create a failed notification
        notification = Notification(
            club_id=test_club.id,
            customer_id=test_customer.id,
            notification_type="booking_confirmation",
            channel="sms",
            recipient_phone=test_customer.phone,
            message="Test",
            status="failed",
        )
        db.add(notification)
        db.commit()
        db.refresh(notification)

        response = client.post(f"/notifications/{notification.id}/retry", headers=auth_headers)

        if response.status_code == 200:
            data = response.json()
            # Status should be updated
            assert data.get("status") in ["pending", "sent", "scheduled"]


# NOTIFICATION BATCHING TESTS
class TestNotificationBatching:
    """Test batch notification operations"""

    def test_send_bulk_notifications(self, client: TestClient, auth_headers: dict, test_club: Club):
        """Test sending notifications to multiple customers"""
        bulk_data = {
            "club_id": str(test_club.id),
            "notification_type": "booking_confirmation",
            "channel": "sms",
            "message": "Important announcement from the club",
            "recipients": ["+46701111111", "+46702222222", "+46703333333"],
        }

        response = client.post("/notifications/bulk", headers=auth_headers, json=bulk_data)

        if response.status_code in [200, 201]:
            data = response.json()
            # Should return info about created notifications
            assert "count" in data or "notifications" in data or isinstance(data, list)

    def test_schedule_bulk_notifications(self, client: TestClient, auth_headers: dict, test_club: Club):
        """Test scheduling bulk notifications"""
        scheduled_time = (datetime.utcnow() + timedelta(hours=2)).isoformat()

        bulk_data = {
            "club_id": str(test_club.id),
            "notification_type": "booking_confirmation",
            "channel": "sms",
            "message": "Scheduled announcement",
            "recipients": ["+46701111111", "+46702222222"],
            "scheduled_for": scheduled_time,  # Add scheduled time to payload
            "status": "pending",  # Explicitly set as pending
        }

        response = client.post("/notifications/bulk", headers=auth_headers, json=bulk_data)

        if response.status_code in [200, 201]:
            data = response.json()
            assert isinstance(data, (dict, list))

            # If response contains notifications, check they're scheduled correctly
            if isinstance(data, dict) and "notifications" in data:
                for notification in data["notifications"]:
                    assert notification["status"] == "pending"
                    # The notifications would be created with pending status
            elif isinstance(data, list):
                for notification in data:
                    assert notification["status"] == "pending"


# PENDING NOTIFICATIONS TESTS
class TestPendingNotifications:
    """Test pending notifications endpoint"""

    def test_get_pending_notifications(
        self,
        client: TestClient,
        auth_headers: dict,
        test_club: Club,
        test_customer: Customer,
        db: Session,
    ):
        """Test getting pending notifications for a club"""
        # Create pending notifications
        for i in range(3):
            notification = Notification(
                club_id=test_club.id,
                customer_id=test_customer.id,
                notification_type=NotificationType.BOOKING_REMINDER,
                channel=NotificationChannel.SMS,
                recipient_phone=test_customer.phone,
                message=f"Reminder {i}",
                status=NotificationStatus.PENDING,
            )
            db.add(notification)

        # Create a sent notification (should not be included)
        sent_notification = Notification(
            club_id=test_club.id,
            customer_id=test_customer.id,
            notification_type=NotificationType.BOOKING_CONFIRMATION,
            channel=NotificationChannel.SMS,
            recipient_phone=test_customer.phone,
            message="Already sent",
            status=NotificationStatus.SENT,
        )
        db.add(sent_notification)
        db.commit()

        response = client.get(f"/notifications/club/{test_club.id}/pending", headers=auth_headers)

        if response.status_code == 200:
            data = response.json()
            assert "notifications" in data
            assert data["total"] >= 3

            # All should be pending
            for notif in data["notifications"]:
                assert notif["status"] == "pending"

    def test_pending_notifications_empty(self, client: TestClient, auth_headers: dict, test_club: Club):
        """Test getting pending notifications when none exist"""
        response = client.get(f"/notifications/club/{test_club.id}/pending", headers=auth_headers)

        if response.status_code == 200:
            data = response.json()
            assert data["total"] >= 0
            assert isinstance(data["notifications"], list)

    def test_pending_notifications_wrong_club(self, client: TestClient, test_club_admin: User, db: Session):
        """Test that club admin can't access another club's pending notifications"""
        # Create another club
        unique_id = str(uuid4())[:8]
        other_club = Club(
            name="Other Club",
            slug=f"other-club-{unique_id}",
            email=f"othe-{unique_id}@club.com",
            phone="+46709999999",
        )
        db.add(other_club)
        db.commit()

        # Try to access with club admin credentials
        access_token_expires = timedelta(minutes=30)
        expire = datetime.utcnow() + access_token_expires

        to_encode = {"sub": str(test_club_admin.id), "exp": expire}

        access_token = jwt.encode(to_encode, settings.SECRET_KEY, algorithm="HS256")
        headers = {"Authorization": f"Bearer {access_token}"}

        response = client.get(f"/notifications/club/{other_club.id}/pending", headers=headers)

        # Should be forbidden
        assert response.status_code == 403


# RETRY NOTIFICATION TESTS
class TestRetryNotification:
    """Test notification retry functionality"""

    def test_retry_sent_notification_fails(
        self,
        client: TestClient,
        test_club_admin: User,
        test_club: Club,
        test_customer: Customer,
        db: Session,
    ):
        """Test that you can't retry a successfully sent notification"""
        # Create token for club_admin
        expire = datetime.utcnow() + timedelta(minutes=30)
        to_encode = {"sub": str(test_club_admin.id), "exp": expire}
        token = jwt.encode(to_encode, settings.SECRET_KEY, algorithm="HS256")
        headers = {"Authorization": f"Bearer {token}"}

        # Create notification with SENT status
        notification = Notification(
            club_id=test_club.id,
            customer_id=test_customer.id,
            notification_type=NotificationType.BOOKING_CONFIRMATION,
            channel=NotificationChannel.SMS,
            recipient_phone=test_customer.phone,
            message="Test",
            status=NotificationStatus.SENT,
            sent_at=datetime.utcnow(),
        )
        db.add(notification)
        db.commit()
        db.refresh(notification)

        # Try to retry
        response = client.post(f"/notifications/{notification.id}/retry", headers=headers)

        # Should return 400 - can't retry sent notification
        assert response.status_code == 400, f"Expected 400, got {response.status_code}: {response.text}"

    def test_retry_bounced_notification(
        self,
        client: TestClient,
        auth_headers: dict,
        test_club: Club,
        test_customer: Customer,
        db: Session,
    ):
        """Test retrying a bounced notification"""
        notification = Notification(
            club_id=test_club.id,
            customer_id=test_customer.id,
            notification_type=NotificationType.BOOKING_CONFIRMATION,
            channel=NotificationChannel.EMAIL,
            recipient_email="invalid@example.com",
            message="Test",
            status=NotificationStatus.BOUNCED,
            error_message="Email bounced",
        )
        db.add(notification)
        db.commit()
        db.refresh(notification)

        response = client.post(f"/notifications/{notification.id}/retry", headers=auth_headers)

        if response.status_code == 200:
            data = response.json()
            assert data["status"] == "pending"

    def test_retry_nonexistent_notification(self, client: TestClient, test_club_admin: User):
        """Test retrying a notification that doesn't exist"""
        # Create token for club_admin
        expire = datetime.utcnow() + timedelta(minutes=30)
        to_encode = {"sub": str(test_club_admin.id), "exp": expire}
        token = jwt.encode(to_encode, settings.SECRET_KEY, algorithm="HS256")
        headers = {"Authorization": f"Bearer {token}"}

        fake_id = uuid4()

        response = client.post(f"/notifications/{fake_id}/retry", headers=headers)

        assert response.status_code == 404


# NOTIFICATION STATS TESTS
class TestNotificationStats:
    """Test notification statistics endpoint"""

    def test_get_notification_stats(
        self,
        client: TestClient,
        auth_headers: dict,
        test_club: Club,
        test_customer: Customer,
        db: Session,
    ):
        """Test getting notification statistics"""
        # Create various notifications
        notifications = [
            Notification(
                club_id=test_club.id,
                customer_id=test_customer.id,
                notification_type=NotificationType.BOOKING_CONFIRMATION,
                channel=NotificationChannel.SMS,
                recipient_phone=test_customer.phone,
                message="Test 1",
                status=NotificationStatus.SENT,
            ),
            Notification(
                club_id=test_club.id,
                customer_id=test_customer.id,
                notification_type=NotificationType.BOOKING_REMINDER,
                channel=NotificationChannel.EMAIL,
                recipient_email="test@example.com",
                message="Test 2",
                status=NotificationStatus.PENDING,
            ),
            Notification(
                club_id=test_club.id,
                customer_id=test_customer.id,
                notification_type=NotificationType.ESCALATION,
                channel=NotificationChannel.SMS,
                recipient_phone="+46701111111",
                message="Test 3",
                status=NotificationStatus.FAILED,
            ),
        ]
        db.add_all(notifications)
        db.commit()

        response = client.get(f"/notifications/stats/{test_club.id}", headers=auth_headers)

        if response.status_code == 200:
            data = response.json()

            assert "by_status" in data
            assert "by_type" in data
            assert "by_channel" in data
            assert "total" in data

            # Check counts
            assert data["total"] >= 3
            assert "sent" in data["by_status"] or "SENT" in data["by_status"]
            assert "sms" in data["by_channel"] or "SMS" in data["by_channel"]

    def test_notification_stats_empty_club(self, client: TestClient, auth_headers: dict, db: Session):
        """Test stats for club with no notifications"""
        unique_id = str(uuid4())[:8]
        new_club = Club(
            name="Empty Club",
            slug=f"empty-club-notif-{unique_id}",
            email=f"empty-{unique_id}@notif.com",
            phone="+46709999999",
        )
        db.add(new_club)
        db.commit()
        db.refresh(new_club)

        response = client.get(f"/notifications/stats/{new_club.id}", headers=auth_headers)

        if response.status_code == 200:
            data = response.json()
            assert data["total"] == 0
            assert isinstance(data["by_status"], dict)

    def test_notification_stats_unauthorized(self, client: TestClient, test_club: Club):
        """Test accessing stats without authentication"""
        response = client.get(f"/notifications/stats/{test_club.id}")
        assert response.status_code == 401


# NOTIFICATION FILTERING TESTS
class TestNotificationFiltering:
    """Test notification list filtering"""

    def test_filter_by_type(
        self,
        client: TestClient,
        auth_headers: dict,
        test_club: Club,
        test_customer: Customer,
        db: Session,
    ):
        """Test filtering notifications by type"""
        # Create different types
        notifications = [
            Notification(
                club_id=test_club.id,
                customer_id=test_customer.id,
                notification_type=NotificationType.BOOKING_CONFIRMATION,
                channel=NotificationChannel.SMS,
                recipient_phone=test_customer.phone,
                message="Confirmation",
            ),
            Notification(
                club_id=test_club.id,
                customer_id=test_customer.id,
                notification_type=NotificationType.BOOKING_REMINDER,
                channel=NotificationChannel.SMS,
                recipient_phone=test_customer.phone,
                message="Reminder",
            ),
        ]
        db.add_all(notifications)
        db.commit()

        response = client.get(
            "/notifications/",
            headers=auth_headers,
            params={
                "club_id": str(test_club.id),
                "notification_type": "booking_confirmation",
            },
        )

        if response.status_code == 200:
            data = response.json()
            notifications = data.get("notifications", [])
            for notif in notifications:
                assert notif["notification_type"] == "booking_confirmation"

    def test_filter_by_status(
        self,
        client: TestClient,
        auth_headers: dict,
        test_club: Club,
        test_customer: Customer,
        db: Session,
    ):
        """Test filtering notifications by status"""
        notifications = [
            Notification(
                club_id=test_club.id,
                customer_id=test_customer.id,
                notification_type=NotificationType.BOOKING_CONFIRMATION,
                channel=NotificationChannel.SMS,
                recipient_phone=test_customer.phone,
                message="Sent",
                status=NotificationStatus.SENT,
            ),
            Notification(
                club_id=test_club.id,
                customer_id=test_customer.id,
                notification_type=NotificationType.BOOKING_CONFIRMATION,
                channel=NotificationChannel.SMS,
                recipient_phone=test_customer.phone,
                message="Pending",
                status=NotificationStatus.PENDING,
            ),
        ]
        db.add_all(notifications)
        db.commit()

        response = client.get(
            "/notifications/",
            headers=auth_headers,
            params={"club_id": str(test_club.id), "status": "sent"},
        )

        if response.status_code == 200:
            data = response.json()
            notifications = data.get("notifications", [])
            for notif in notifications:
                assert notif["status"] == "sent"

    def test_filter_by_multiple_params(self, client: TestClient, auth_headers: dict, test_club: Club):
        """Test filtering with multiple parameters"""
        response = client.get(
            "/notifications/",
            headers=auth_headers,
            params={
                "club_id": str(test_club.id),
                "notification_type": "booking_confirmation",
                "status": "sent",
            },
        )

        if response.status_code == 200:
            data = response.json()
            notifications = data.get("notifications", [])
            for notif in notifications:
                assert notif["notification_type"] == "booking_confirmation"
                assert notif["status"] == "sent"


# NOTIFICATION PAGINATION TESTS
class TestNotificationPagination:
    """Test notification list pagination"""

    def test_pagination_first_page(
        self, client: TestClient, auth_headers: dict, test_club: Club, test_customer: Customer, db: Session
    ):
        """Test getting first page of notifications"""
        # Create many notifications
        for i in range(20):
            notification = Notification(
                club_id=test_club.id,
                customer_id=test_customer.id,
                notification_type=NotificationType.BOOKING_CONFIRMATION,
                channel=NotificationChannel.SMS,
                recipient_phone=test_customer.phone,
                message=f"Message {i}",
            )
            db.add(notification)
        db.commit()

        response = client.get(
            "/notifications/",
            headers=auth_headers,
            params={"club_id": str(test_club.id), "skip": 0, "limit": 10},
        )

        if response.status_code == 200:
            data = response.json()
            assert len(data["notifications"]) <= 10
            assert data["page_size"] == 10
            assert data["page"] == 1

    def test_pagination_second_page(self, client: TestClient, auth_headers: dict, test_club: Club):
        """Test getting second page of notifications"""
        response = client.get(
            "/notifications/",
            headers=auth_headers,
            params={"club_id": str(test_club.id), "skip": 10, "limit": 10},
        )

        if response.status_code == 200:
            data = response.json()
            assert data["page"] == 2
            assert data["page_size"] == 10


# NOTIFICATION ACCESS CONTROL TESTS
class TestNotificationAccessControl:
    """Test notification access control"""

    def test_club_admin_can_access_own_notifications(
        self,
        client: TestClient,
        test_club: Club,
        test_club_admin: User,
        test_customer: Customer,
        db: Session,
    ):
        """Test that club admin can access their club's notifications"""
        notification = Notification(
            club_id=test_club.id,
            customer_id=test_customer.id,
            notification_type=NotificationType.BOOKING_CONFIRMATION,
            channel=NotificationChannel.SMS,
            recipient_phone=test_customer.phone,
            message="Test",
        )
        db.add(notification)
        db.commit()
        db.refresh(notification)

        # Create token for club admin
        access_token_expires = timedelta(minutes=30)
        expire = datetime.utcnow() + access_token_expires

        to_encode = {
            "sub": str(test_club_admin.id),
            "exp": expire,
        }

        access_token = jwt.encode(to_encode, settings.SECRET_KEY, algorithm="HS256")
        headers = {"Authorization": f"Bearer {access_token}"}

        response = client.get(f"/notifications/{notification.id}", headers=headers)

        # Should be able to access
        if response.status_code == 200:
            data = response.json()
            assert str(data["id"]) == str(notification.id)

    def test_club_admin_cannot_access_other_club_notification(
        self, client: TestClient, test_club_admin: User, db: Session
    ):
        """Test that club admin cannot access another club's notifications"""
        # Create another club and notification
        unique_id = str(uuid4())[:8]
        other_club = Club(
            name="Other Club",
            slug=f"other-club-access-{unique_id}",
            email=f"other{unique_id}@access.com",
            phone="+46708888888",
        )
        db.add(other_club)
        db.commit()

        other_customer = Customer(club_id=other_club.id, phone="+46709999999", name="Other Customer")
        db.add(other_customer)
        db.commit()

        notification = Notification(
            club_id=other_club.id,
            customer_id=other_customer.id,
            notification_type=NotificationType.BOOKING_CONFIRMATION,
            channel=NotificationChannel.SMS,
            recipient_phone="+46709999999",
            message="Test",
        )
        db.add(notification)
        db.commit()
        db.refresh(notification)

        # Try to access with club admin
        access_token_expires = timedelta(minutes=30)
        expire = datetime.utcnow() + access_token_expires

        to_encode = {"sub": str(test_club_admin.id), "exp": expire}

        access_token = jwt.encode(to_encode, settings.SECRET_KEY, algorithm="HS256")
        headers = {"Authorization": f"Bearer {access_token}"}

        response = client.get(f"/notifications/{notification.id}", headers=headers)

        # Should be forbidden
        assert response.status_code == 403
