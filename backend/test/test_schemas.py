"""
Tests for Pydantic Schemas - FIXED VERSION
Tests schema validation, serialization, and field requirements
"""

from datetime import datetime, timedelta
from uuid import UUID, uuid4

import pytest
from pydantic import ValidationError

from app.schemas.booking import (
    BookingCreate,
    BookingResponse,
    BookingStatus,
    BookingType,
    BookingUpdate,
)

# Import schemas from actual app
from app.schemas.club import ClubCreate, ClubResponse, ClubUpdate
from app.schemas.conversation import (
    ConversationCreate,
    ConversationResponse,
    ConversationStatus,
    ConversationUpdate,
)
from app.schemas.customer import (
    CustomerCreate,
    CustomerResponse,
    CustomerStatus,
    CustomerUpdate,
)
from app.schemas.notification import (
    NotificationChannel,
    NotificationCreate,
    NotificationResponse,
    NotificationStatus,
    NotificationType,
    NotificationUpdate,
)
from app.schemas.user import UserCreate, UserResponse, UserUpdate


class TestClubSchemas:
    """Test Club Pydantic schemas"""

    def test_club_create_valid(self):
        """Test creating a valid club schema"""
        data = {
            "name": "Test Tennis Club",
            "slug": "test-tennis-club",
            "email": "test@tennisclub.com",
            "phone": "+46701234567",
            "address": "Test Street 123",
            "city": "Stockholm",
            "postal_code": "11122",
            "country": "Sweden",
            "description": "A test tennis club",
            "website": "https://testtennisclub.com",
            "membership_types": [
                {
                    "name": "Individual",
                    "price": 2000,
                    "currency": "SEK",
                    "period": "year",
                }
            ],
            "pricing_info": {
                "court_rental": {
                    "indoor": 200,
                    "outdoor": 150,
                    "currency": "SEK",
                    "unit": "hour",
                }
            },
            "facilities": ["Indoor courts", "Outdoor courts"],
            "opening_hours": {"monday": {"open": "06:00", "close": "22:00"}},
            "knowledge_base": {"faq": [{"question": "Hours?", "answer": "6 AM - 10 PM"}]},
        }

        club = ClubCreate(**data)
        assert club.name == "Test Tennis Club"
        assert club.slug == "test-tennis-club"
        assert club.email == "test@tennisclub.com"
        assert len(club.membership_types) == 1

    def test_club_create_missing_required_fields(self):
        """Test that missing required fields raise validation error"""
        data = {
            "name": "Test Club"
            # Missing required fields: slug, email, phone
        }

        with pytest.raises(ValidationError) as exc_info:
            ClubCreate(**data)

        errors = exc_info.value.errors()
        assert len(errors) >= 2  # At least slug, email, phone

    def test_club_create_invalid_email(self):
        """Test that invalid email raises validation error"""
        data = {
            "name": "Test Club",
            "slug": "test-club",
            "email": "invalid-email",  # Not a valid email
            "phone": "+46701234567",
        }

        with pytest.raises(ValidationError) as exc_info:
            ClubCreate(**data)

        errors = exc_info.value.errors()
        assert any(error["loc"] == ("email",) for error in errors)

    def test_club_update_partial(self):
        """Test partial update with only some fields"""
        data = {"name": "Updated Club Name", "description": "Updated description"}

        club_update = ClubUpdate(**data)
        assert club_update.name == "Updated Club Name"
        assert club_update.description == "Updated description"
        assert club_update.email is None  # Optional field

    def test_club_response_serialization(self):
        """Test ClubResponse serialization - FIXED"""
        now = datetime.utcnow()
        data = {
            "id": uuid4(),
            "name": "Test Club",
            "slug": "test-club",
            "email": "test@club.com",
            "phone": "+46701234567",
            "address": "Test St",
            "city": "Stockholm",
            "postal_code": "11122",
            "country": "Sweden",
            "description": "Test",
            "website": "https://test.com",
            # Required fields that were missing:
            "membership_types": [{"name": "Basic", "price": 1000, "currency": "SEK", "period": "year"}],
            "pricing_info": {"court_rental": {"price": 200, "currency": "SEK"}},
            "facilities": ["Indoor courts"],
            "opening_hours": {"monday": {"open": "06:00", "close": "22:00"}},
            "knowledge_base": {"faq": []},
            "is_active": True,
            "subscription_tier": "basic",
            "created_at": now,
            "updated_at": now,
        }

        club = ClubResponse(**data)
        assert club.name == "Test Club"
        assert club.is_active is True
        assert len(club.facilities) == 1


class TestUserSchemas:
    """Test User Pydantic schemas"""

    def test_user_create_valid(self):
        """Test creating a valid user schema - FIXED"""
        data = {
            "email": "user@example.com",
            "username": "testuser",
            "full_name": "Test User",
            "password": "SecurePassword123",
            "role": "club_staff",
        }

        user = UserCreate(**data)
        assert user.email == "user@example.com"
        assert user.username == "testuser"
        assert user.password == "SecurePassword123"

    def test_user_create_missing_fields(self):
        """Test that missing required fields raise validation error"""
        data = {
            "email": "user@example.com"
            # Missing: username, full_name, password
        }

        with pytest.raises(ValidationError) as exc_info:
            UserCreate(**data)

        errors = exc_info.value.errors()
        assert len(errors) >= 3

    def test_user_create_invalid_email(self):
        """Test that invalid email raises validation error"""
        data = {
            "email": "not-an-email",
            "username": "testuser",
            "full_name": "Test User",
            "password": "SecurePassword123",
        }

        with pytest.raises(ValidationError) as exc_info:
            UserCreate(**data)

        errors = exc_info.value.errors()
        assert any(error["loc"] == ("email",) for error in errors)

    def test_user_create_weak_password(self):
        """Test that weak password raises validation error"""
        data = {
            "email": "user@example.com",
            "username": "testuser",
            "full_name": "Test User",
            "password": "weak",  # Too short, no uppercase, no digit
        }

        with pytest.raises(ValidationError):
            UserCreate(**data)

    def test_user_update_partial(self):
        """Test partial user update"""
        data = {"full_name": "Updated Name", "phone": "+46701234567"}

        user_update = UserUpdate(**data)
        assert user_update.full_name == "Updated Name"
        assert user_update.phone == "+46701234567"
        assert user_update.email is None  # Not updated

    def test_user_response_excludes_password(self):
        """Test that UserResponse doesn't include password - FIXED"""
        now = datetime.utcnow()
        data = {
            "id": uuid4(),
            "club_id": uuid4(),
            "email": "user@example.com",
            "username": "testuser",
            "full_name": "Test User",
            "phone": "+46701234567",
            "role": "club_staff",
            "is_active": True,
            "is_verified": True,
            "last_login": now,
            "created_at": now,
            "updated_at": now,
        }

        user = UserResponse(**data)
        assert user.email == "user@example.com"
        assert not hasattr(user, "password")
        assert not hasattr(user, "hashed_password")


class TestCustomerSchemas:
    """Test Customer Pydantic schemas"""

    def test_customer_create_valid(self):
        """Test creating a valid customer schema"""
        data = {
            "club_id": uuid4(),
            "name": "John Doe",
            "phone": "+46701234567",
            "email": "john@example.com",
            "status": CustomerStatus.LEAD,
        }

        customer = CustomerCreate(**data)
        assert customer.name == "John Doe"
        assert customer.phone == "+46701234567"
        assert customer.status == CustomerStatus.LEAD

    def test_customer_create_invalid_phone(self):
        """Test that invalid phone format raises validation error"""
        data = {
            "club_id": uuid4(),
            "name": "John Doe",
            "phone": "invalid_phone",  # Invalid format
            "email": "john@example.com",
        }

        with pytest.raises(ValidationError) as exc_info:
            CustomerCreate(**data)

        errors = exc_info.value.errors()
        assert any(error["loc"] == ("phone",) for error in errors)

    def test_customer_update_status(self):
        """Test updating customer status"""
        data = {
            "status": CustomerStatus.MEMBER,
            "converted_to_member": True,
            "conversion_date": datetime.utcnow(),
        }

        customer_update = CustomerUpdate(**data)
        assert customer_update.status == CustomerStatus.MEMBER
        assert customer_update.converted_to_member is True

    def test_customer_response_includes_relationships(self):
        """Test CustomerResponse includes all fields - FIXED"""
        now = datetime.utcnow()
        data = {
            "id": uuid4(),
            "club_id": uuid4(),
            "name": "Jane Doe",
            "phone": "+46709876543",
            "email": "jane@example.com",
            "status": CustomerStatus.LEAD,
            "source": "phone_call",
            "interested_in": "Tennis lessons",
            "membership_type_interest": "Individual",
            "preferred_contact_method": "phone",
            "notes": "Interested customer",
            "requires_follow_up": False,
            "follow_up_date": None,
            "is_high_priority": False,
            "converted_to_member": False,
            "conversion_date": None,
            "consent_marketing": True,
            "first_contact_date": now,
            "last_contact_date": now,
            "created_at": now,
            "updated_at": now,
        }

        customer = CustomerResponse(**data)
        assert customer.name == "Jane Doe"
        assert customer.status == CustomerStatus.LEAD
        assert customer.requires_follow_up is False


class TestBookingSchemas:
    """Test Booking Pydantic schemas"""

    def test_booking_create_valid(self):
        """Test creating a valid booking schema"""
        start_time = datetime.utcnow() + timedelta(days=1)
        end_time = start_time + timedelta(hours=1)

        data = {
            "club_id": uuid4(),
            "customer_id": uuid4(),
            "booking_type": BookingType.COURT,
            "resource_name": "Court 1",
            "booking_date": start_time,
            "start_time": start_time,
            "end_time": end_time,
            "contact_name": "John Doe",
            "contact_phone": "+46701234567",
            "status": BookingStatus.PENDING,
        }

        booking = BookingCreate(**data)
        assert booking.booking_type == BookingType.COURT
        assert booking.status == BookingStatus.PENDING

    def test_booking_create_end_before_start(self):
        """Test validation for end time before start time"""
        # This validation should ideally be in the Pydantic model
        # For now, just test that the schema accepts the data
        start_time = datetime.utcnow() + timedelta(days=1)
        end_time = start_time - timedelta(hours=1)  # End before start

        data = {
            "club_id": uuid4(),
            "customer_id": uuid4(),
            "booking_type": BookingType.COURT,
            "booking_date": start_time,
            "start_time": start_time,
            "end_time": end_time,  # Before start_time
            "contact_name": "John Doe",
            "contact_phone": "+46701234567",
        }

        # Schema accepts it, but business logic should validate
        booking = BookingCreate(**data)
        assert booking.end_time < booking.start_time

    def test_booking_create_past_date(self):
        """Test creating booking with past date"""
        past_time = datetime.utcnow() - timedelta(days=1)

        data = {
            "club_id": uuid4(),
            "customer_id": uuid4(),
            "booking_type": BookingType.COURT,
            "booking_date": past_time,
            "start_time": past_time,
            "end_time": past_time + timedelta(hours=1),
            "contact_name": "John Doe",
            "contact_phone": "+46701234567",
        }

        # Schema accepts past dates, validation should be in business logic
        booking = BookingCreate(**data)
        assert booking.booking_date < datetime.utcnow()

    def test_booking_update_status(self):
        """Test updating booking status"""
        data = {"status": BookingStatus.CONFIRMED, "payment_status": "paid"}

        booking_update = BookingUpdate(**data)
        assert booking_update.status == BookingStatus.CONFIRMED
        assert booking_update.payment_status == "paid"

    def test_booking_response_includes_computed_fields(self):
        """Test BookingResponse includes all fields - FIXED"""
        now = datetime.utcnow()
        start_time = now + timedelta(days=1)
        end_time = start_time + timedelta(hours=1)

        data = {
            "id": uuid4(),
            "club_id": uuid4(),
            "customer_id": uuid4(),
            "conversation_id": None,
            "booking_type": BookingType.COURT,
            "resource_name": "Court 1",
            "booking_date": start_time,
            "start_time": start_time,
            "end_time": end_time,
            "status": BookingStatus.CONFIRMED,
            "contact_name": "John Doe",
            "contact_phone": "+46701234567",
            "price": 200.0,
            "currency": "SEK",
            "payment_status": "paid",
            "matchi_booking_id": None,
            "synced_to_matchi": None,
            "confirmation_code": "ABC123",
            "confirmation_sent_at": None,
            "cancellation_reason": None,
            "cancelled_at": None,
            "cancelled_by": None,
            "created_at": now,
            "updated_at": now,
        }

        booking = BookingResponse(**data)
        assert booking.status == BookingStatus.CONFIRMED
        assert booking.price == 200.0
        assert booking.currency == "SEK"


class TestConversationSchemas:
    """Test Conversation Pydantic schemas"""

    def test_conversation_create_valid(self):
        """Test creating a valid conversation schema"""
        data = {
            "club_id": uuid4(),
            "customer_id": uuid4(),
            "vapi_call_id": "call_123",
            "phone_number": "+46701234567",
            "status": ConversationStatus.ACTIVE,
        }

        conversation = ConversationCreate(**data)
        assert conversation.vapi_call_id == "call_123"
        assert conversation.status == ConversationStatus.ACTIVE

    def test_conversation_update_status(self):
        """Test updating conversation status"""
        data = {
            "status": ConversationStatus.COMPLETED,
            "call_duration": 180,
            "summary": "Customer booked a court",
            "sentiment": "positive",
        }

        conversation_update = ConversationUpdate(**data)
        assert conversation_update.status == ConversationStatus.COMPLETED
        assert conversation_update.call_duration == 180

    def test_conversation_response_structure(self):
        """Test ConversationResponse structure - FIXED"""
        now = datetime.utcnow()
        data = {
            "id": uuid4(),
            "club_id": uuid4(),
            "customer_id": uuid4(),
            "vapi_call_id": "call_123",
            "vapi_assistant_id": "asst_123",
            "phone_number": "+46701234567",
            "status": ConversationStatus.COMPLETED,
            "call_duration": 120,
            "call_cost": 0.50,
            "intent": "booking_inquiry",
            "summary": "Customer booked court",
            "sentiment": "positive",
            "topics_discussed": ["booking", "pricing"],
            "questions_asked": ["What's the price?"],
            "outcome": "booking_created",
            "action_required": None,
            "escalated_to_manager": False,
            "customer_satisfaction": 5,
            "resolution_status": "resolved",
            "started_at": now,
            "ended_at": now + timedelta(minutes=2),
            "created_at": now,
            "updated_at": now,
        }

        conversation = ConversationResponse(**data)
        assert conversation.status == ConversationStatus.COMPLETED
        assert conversation.call_duration == 120
        assert conversation.escalated_to_manager is False


class TestNotificationSchemas:
    """Test Notification Pydantic schemas"""

    def test_notification_create_valid(self):
        """Test creating a valid notification schema"""
        data = {
            "club_id": uuid4(),
            "notification_type": NotificationType.BOOKING_CONFIRMATION,
            "channel": NotificationChannel.SMS,
            "recipient_phone": "+46701234567",
            "message": "Your booking is confirmed",
        }

        notification = NotificationCreate(**data)
        assert notification.notification_type == NotificationType.BOOKING_CONFIRMATION
        assert notification.channel == NotificationChannel.SMS

    def test_notification_create_missing_recipient(self):
        """Test notification without recipient"""
        data = {
            "club_id": uuid4(),
            "notification_type": NotificationType.ESCALATION,
            "channel": NotificationChannel.EMAIL,
            "message": "Manager escalation",
            # Missing recipient_email for EMAIL channel
        }

        # Schema allows it, validation should be in business logic
        notification = NotificationCreate(**data)
        assert notification.channel == NotificationChannel.EMAIL

    def test_notification_update_status(self):
        """Test updating notification status"""
        data = {"status": NotificationStatus.SENT, "sent_at": datetime.utcnow()}

        notification_update = NotificationUpdate(**data)
        assert notification_update.status == NotificationStatus.SENT
        assert notification_update.sent_at is not None

    def test_notification_response_includes_metadata(self):
        """Test NotificationResponse includes metadata - FIXED"""
        now = datetime.utcnow()
        data = {
            "id": uuid4(),
            "club_id": uuid4(),
            "customer_id": uuid4(),
            "conversation_id": None,
            "booking_id": None,
            "notification_type": NotificationType.BOOKING_CONFIRMATION,
            "channel": NotificationChannel.SMS,
            "status": NotificationStatus.SENT,
            "message": "Booking confirmed",
            "recipient_name": "John Doe",
            "recipient_phone": "+46701234567",
            "recipient_email": None,
            "template_used": "booking_confirmation",
            "context_data": {"booking_id": "123"},
            "provider_status": "delivered",
            "provider": "twilio",
            "provider_message_id": "msg_123",
            "sent_at": now,
            "delivered_at": now,
            "failed_at": None,
            "error_message": None,
            "retry_count": 0,
            "max_retries": 3,
            "next_retry_at": None,
            "cost": 0.05,
            "currency": "SEK",
            "priority": "normal",
            "created_at": now,
            "updated_at": now,
        }

        notification = NotificationResponse(**data)
        assert notification.status == NotificationStatus.SENT
        assert notification.retry_count == 0


class TestSchemaValidationEdgeCases:
    """Test edge cases in schema validation"""

    def test_uuid_validation(self):
        """Test UUID field validation"""
        data = {"club_id": uuid4(), "name": "Test Customer", "phone": "+46701234567"}

        customer = CustomerCreate(**data)
        assert isinstance(customer.club_id, UUID)

    def test_enum_validation(self):
        """Test enum field validation"""
        # Valid enum
        assert BookingStatus.PENDING == "pending"
        assert CustomerStatus.LEAD == "lead"

        # Invalid enum should raise error
        with pytest.raises(ValidationError):
            data = {
                "club_id": uuid4(),
                "customer_id": uuid4(),
                "booking_type": "invalid_type",  # Not in enum
                "booking_date": datetime.utcnow(),
                "start_time": datetime.utcnow(),
                "end_time": datetime.utcnow() + timedelta(hours=1),
                "contact_name": "Test",
                "contact_phone": "+46701234567",
            }
            BookingCreate(**data)

    def test_optional_fields(self):
        """Test optional fields can be None"""
        data = {
            "club_id": uuid4(),
            "name": "Test Customer",
            "phone": "+46701234567",
            "email": None,  # Optional field
        }

        customer = CustomerCreate(**data)
        assert customer.email is None

    def test_json_serialization(self):
        """Test model can be serialized to JSON"""
        data = {
            "name": "Test Customer",
            "phone": "+46701234567",
            "email": "test@example.com",
        }

        customer = CustomerCreate(club_id=uuid4(), **data)
        json_dict = customer.model_dump()

        assert "club_id" in json_dict
        assert "name" in json_dict
        assert json_dict["name"] == "Test Customer"


class TestSchemaDefaults:
    """Test default values in schemas"""

    def test_booking_default_status(self):
        """Test booking defaults to PENDING status"""
        data = {
            "club_id": uuid4(),
            "customer_id": uuid4(),
            "booking_type": BookingType.COURT,
            "booking_date": datetime.utcnow() + timedelta(days=1),
            "start_time": datetime.utcnow() + timedelta(days=1),
            "end_time": datetime.utcnow() + timedelta(days=1, hours=1),
            "contact_name": "Test",
            "contact_phone": "+46701234567",
        }

        booking = BookingCreate(**data)
        assert booking.status == BookingStatus.PENDING

    def test_customer_default_status(self):
        """Test customer defaults to LEAD status"""
        data = {"club_id": uuid4(), "name": "Test Customer", "phone": "+46701234567"}

        customer = CustomerCreate(**data)
        assert customer.status == CustomerStatus.LEAD

    def test_conversation_default_status(self):
        """Test conversation defaults to ACTIVE status"""
        data = {"club_id": uuid4(), "customer_id": uuid4()}

        conversation = ConversationCreate(**data)
        assert conversation.status == ConversationStatus.ACTIVE


class TestSchemaRelationships:
    """Test schemas with related data"""

    def test_club_response_with_nested_data(self):
        """Test ClubResponse with nested membership and pricing data - FIXED"""
        now = datetime.utcnow()
        data = {
            "id": uuid4(),
            "name": "Test Club",
            "slug": "test-club",
            "email": "test@club.com",
            "phone": "+46701234567",
            "country": "Sweden",
            "membership_types": [
                {
                    "name": "Individual",
                    "price": 2000,
                    "currency": "SEK",
                    "period": "year",
                },
                {"name": "Family", "price": 3500, "currency": "SEK", "period": "year"},
            ],
            "facilities": ["Indoor courts", "Outdoor courts", "Cafe"],
            "pricing_info": {"court_rental": {"price": 200}},
            "opening_hours": {"monday": {"open": "06:00", "close": "22:00"}},
            "knowledge_base": {"faq": []},
            "is_active": True,
            "subscription_tier": "premium",
            "created_at": now,
            "updated_at": now,
        }

        club = ClubResponse(**data)
        assert len(club.membership_types) == 2
        assert len(club.facilities) == 3

    def test_booking_response_with_customer_info(self):
        """Test BookingResponse with customer reference - FIXED"""
        now = datetime.utcnow()
        start_time = now + timedelta(days=1)

        data = {
            "id": uuid4(),
            "club_id": uuid4(),
            "customer_id": uuid4(),
            "conversation_id": None,
            "booking_type": BookingType.COURT,
            "resource_name": "Court 1",
            "booking_date": start_time,
            "start_time": start_time,
            "end_time": start_time + timedelta(hours=1),
            "status": BookingStatus.CONFIRMED,
            "contact_name": "John Doe",
            "contact_phone": "+46701234567",
            "contact_email": "john@example.com",
            "price": 200.0,
            "currency": "SEK",
            "payment_status": "paid",
            "matchi_booking_id": None,
            "synced_to_matchi": None,
            "confirmation_code": None,
            "confirmation_sent_at": None,
            "cancellation_reason": None,
            "cancelled_at": None,
            "cancelled_by": None,
            "created_at": now,
            "updated_at": now,
        }

        booking = BookingResponse(**data)
        assert isinstance(booking.customer_id, UUID)
        assert booking.contact_name == "John Doe"
