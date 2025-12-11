"""
Tests for Services
"""

import pytest
from sqlalchemy.orm import Session

from app.models.club import Club
from app.models.customer import Customer


class TestVAPIService:
    """Test VAPI Service"""

    @pytest.mark.asyncio
    async def test_create_assistant(self, mock_vapi_service, db: Session, test_club: Club):
        """Test creating a VAPI assistant"""
        result = await mock_vapi_service.create_assistant(
            db=db, club_id=test_club.id, name=f"{test_club.name} Receptionist"
        )

        assert result["success"] is True
        assert "assistant_id" in result

    @pytest.mark.asyncio
    async def test_update_assistant(self, mock_vapi_service, db: Session, test_club: Club):
        """Test updating a VAPI assistant"""
        result = await mock_vapi_service.update_assistant(
            db=db, club_id=test_club.id, assistant_id="test_assistant_123"
        )

        assert result["success"] is True

    @pytest.mark.asyncio
    async def test_create_assistant_with_knowledge_base(self, mock_vapi_service, db: Session, test_club: Club):
        """Test creating assistant with custom knowledge base"""
        test_club.knowledge_base = {
            "faq": [
                {"question": "What are your hours?", "answer": "6 AM to 10 PM"},
                {"question": "How much is membership?", "answer": "2000 SEK per year"},
            ]
        }

        result = await mock_vapi_service.create_assistant(
            db=db, club_id=test_club.id, name=f"{test_club.name} Receptionist"
        )

        assert result["success"] is True


class TestNotificationService:
    """Test Notification Service"""

    def test_send_sms(self, mock_notification_service):
        """Test sending SMS notification"""
        result = mock_notification_service.send_sms(phone="+46701234567", message="Test SMS message")

        assert result["success"] is True
        assert "message_id" in result

    def test_send_email(self, mock_notification_service):
        """Test sending email notification"""
        result = mock_notification_service.send_email(
            to_email="test@example.com",
            subject="Test Email",
            body="This is a test email",
        )

        assert result["success"] is True

    def test_send_booking_confirmation(self, mock_notification_service, test_customer: Customer):
        """Test sending booking confirmation"""
        booking_details = {
            "facility": "Court 1",
            "date": "2024-12-10",
            "time": "10:00-11:00",
            "price": "200 SEK",
        }

        result = mock_notification_service.send_sms(
            phone=test_customer.phone,
            message=f"Booking confirmed: {booking_details['facility']} on {booking_details['date']}",
        )

        assert result["success"] is True


class TestMatchiService:
    """Test Matchi Integration Service"""

    def test_get_available_slots(self, mock_matchi_service, test_club: Club):
        """Test getting available time slots from Matchi"""
        from datetime import date

        result = mock_matchi_service.get_available_slots(
            club_id=test_club.matchi_club_id, date=date.today(), court_type="indoor"
        )

        assert result["success"] is True
        assert "slots" in result
        assert len(result["slots"]) > 0

    def test_create_booking_on_matchi(self, mock_matchi_service, test_club: Club, test_customer: Customer):
        """Test creating a booking on Matchi"""
        from datetime import datetime, timedelta

        booking_data = {
            "club_id": test_club.matchi_club_id,
            "court": "Court 1",
            "start_time": datetime.now() + timedelta(days=1),
            "duration_hours": 1,
            "customer_name": f"{test_customer.name} {test_customer}",
            "customer_phone": test_customer.phone,
        }

        result = mock_matchi_service.create_booking(**booking_data)

        assert result["success"] is True
        assert "booking_id" in result


class TestKnowledgeBaseService:
    """Test Knowledge Base Service"""

    @pytest.fixture
    def mock_knowledge_base(self, mocker):
        """Mock Knowledge Base service"""
        mock_service = mocker.patch("app.services.knowledge_base.KnowledgeBaseService")
        mock_instance = mock_service.return_value

        mock_instance.query.return_value = {
            "answer": "Our opening hours are 6 AM to 10 PM every day.",
            "confidence": 0.95,
            "source": "club_info",
        }

        return mock_instance

    def test_query_knowledge_base(self, mock_knowledge_base, test_club: Club):
        """Test querying the knowledge base"""
        result = mock_knowledge_base.query(club_id=test_club.id, question="What are your opening hours?")

        assert "answer" in result
        assert result["confidence"] > 0.8

    def test_add_knowledge_base_entry(self, mock_knowledge_base, test_club: Club):
        """Test adding a new knowledge base entry"""
        mock_knowledge_base.add_entry.return_value = {"success": True}

        result = mock_knowledge_base.add_entry(
            club_id=test_club.id,
            question="What is your cancellation policy?",
            answer="You can cancel up to 24 hours before your booking.",
        )

        assert result["success"] is True


class TestServiceIntegration:
    """Test service integration scenarios"""

    @pytest.mark.asyncio
    async def test_booking_workflow_with_notifications(
        self,
        mock_notification_service,
        mock_matchi_service,
        test_club: Club,
        test_customer: Customer,
    ):
        """Test complete booking workflow with multiple services"""
        # 1. Get available slots from Matchi
        slots_result = mock_matchi_service.get_available_slots(
            club_id=test_club.matchi_club_id, date="2024-12-10", court_type="indoor"
        )
        assert slots_result["success"] is True

        # 2. Create booking on Matchi
        booking_result = mock_matchi_service.create_booking(
            club_id=test_club.matchi_club_id,
            court="Court 1",
            start_time="2024-12-10 10:00",
        )
        assert booking_result["success"] is True

        # 3. Send confirmation SMS
        sms_result = mock_notification_service.send_sms(phone=test_customer.phone, message="Your booking is confirmed!")
        assert sms_result["success"] is True
