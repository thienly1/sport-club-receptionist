"""
Test Utilities and Helper Functions
This module provides utility functions and helpers for testing.
"""

import random
import string
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from uuid import uuid4

from faker import Faker
from jose import jwt
from passlib.context import CryptContext

from app.models.booking import Booking
from app.models.club import Club
from app.models.conversation import Conversation
from app.models.customer import Customer
from app.models.notification import Notification
from app.models.user import User

fake = Faker()


class TestDataGenerator:
    """Generate test data for various models"""

    @staticmethod
    def generate_club_data(override: Optional[Dict] = None) -> Dict:
        """Generate random club data"""
        slug = "".join(random.choices(string.ascii_lowercase + string.digits, k=10))
        data = {
            "name": fake.company(),
            "slug": slug,
            "email": fake.email(),
            "phone": fake.phone(),
            "address": fake.address(),
            "city": fake.city(),
            "postal_code": fake.postcode(),
            "country": "Sweden",
            "description": fake.text(max_nb_chars=200),
            "website": fake.url(),
            "membership_types": ["Standard", "Premium", "VIP"],
            "pricing_info": {"court_hour": 200, "membership_monthly": 500},
            "facilities": ["Court 1", "Court 2", "Changing Rooms"],
            "opening_hours": {
                "monday": "09:00-21:00",
                "tuesday": "09:00-21:00",
                "wednesday": "09:00-21:00",
                "thursday": "09:00-21:00",
                "friday": "09:00-21:00",
                "saturday": "10:00-18:00",
                "sunday": "10:00-18:00",
            },
        }

        if override:
            data.update(override)

        return data

    @staticmethod
    def generate_customer_data(club_id: str, override: Optional[Dict] = None) -> Dict:
        """Generate random customer data"""
        data = {
            "club_id": club_id,
            "name": fake.name(),
            "last_name": fake(),
            "phone": fake.phone(),
            "email": fake.email(),
            "date_of_birth": fake.date_of_birth(minimum_age=18, maximum_age=80).isoformat(),
            "address": fake.address(),
            "membership_status": random.choice(["active", "inactive", "pending"]),
            "membership_type": random.choice(["Standard", "Premium", "VIP"]),
            "preferences": {
                "preferred_court": random.choice(["Court 1", "Court 2"]),
                "notification_method": random.choice(["sms", "email", "both"]),
            },
        }

        if override:
            data.update(override)

        return data

    @staticmethod
    def generate_booking_data(
        club_id: str,
        customer_id: str,
        days_ahead: int = 1,
        override: Optional[Dict] = None,
    ) -> Dict:
        """Generate random booking data"""
        start_time = datetime.utcnow() + timedelta(days=days_ahead, hours=random.randint(9, 18))
        duration = random.choice([1, 1.5, 2])

        data = {
            "club_id": club_id,
            "customer_id": customer_id,
            "court_name": f"Court {random.randint(1, 3)}",
            "start_time": start_time.isoformat(),
            "end_time": (start_time + timedelta(hours=duration)).isoformat(),
            "status": random.choice(["pending", "confirmed"]),
            "booking_type": random.choice(["regular", "tournament", "training"]),
            "notes": fake.sentence() if random.random() > 0.5 else None,
        }

        if override:
            data.update(override)

        return data

    @staticmethod
    def generate_user_data(club_id: Optional[str] = None, override: Optional[Dict] = None) -> Dict:
        """Generate random user data"""
        data = {
            "email": fake.email(),
            "username": fake.user_name(),
            "password": "Test123!@#",
            "full_name": fake.name(),
            "role": random.choice(["club_admin", "club_staff"]),
            "is_active": True,
        }

        if club_id:
            data["club_id"] = club_id

        if override:
            data.update(override)

        return data


class TestHelpers:
    """Helper functions for tests"""

    @staticmethod
    def create_auth_token(user_data: Dict, secret_key: str = "test_secret_key") -> str:
        """Create JWT token for testing"""
        to_encode = {
            "sub": user_data.get("email") or user_data.get("username"),
            "user_id": str(user_data.get("id", uuid4())),
            "role": user_data.get("role", "club_admin"),
            "exp": datetime.utcnow() + timedelta(hours=1),
        }

        return jwt.encode(to_encode, secret_key, algorithm="HS256")

    @staticmethod
    def create_auth_headers(token: str) -> Dict[str, str]:
        """Create authorization headers"""
        return {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}

    @staticmethod
    def assert_response_success(response, expected_status: int = 200):
        """Assert response is successful"""
        assert (
            response.status_code == expected_status
        ), f"Expected {expected_status}, got {response.status_code}: {response.text}"

    @staticmethod
    def assert_response_error(response, expected_status: int = 400):
        """Assert response is an error"""
        assert response.status_code == expected_status, f"Expected {expected_status}, got {response.status_code}"

    @staticmethod
    def assert_has_keys(data: Dict, keys: List[str]):
        """Assert dictionary has all specified keys"""
        for key in keys:
            assert key in data, f"Missing key: {key}"

    @staticmethod
    def assert_valid_uuid(value: str):
        """Assert value is a valid UUID"""
        try:
            uuid4_obj = uuid4()
            assert len(value) == len(str(uuid4_obj))
        except (ValueError, AssertionError):
            raise AssertionError(f"Invalid UUID: {value}")

    @staticmethod
    def assert_valid_datetime(value: str):
        """Assert value is a valid ISO datetime"""
        try:
            datetime.fromisoformat(value.replace("Z", "+00:00"))
        except ValueError:
            raise AssertionError(f"Invalid datetime: {value}")

    @staticmethod
    def create_future_datetime(days: int = 1, hours: int = 0) -> datetime:
        """Create a future datetime"""
        return datetime.utcnow() + timedelta(days=days, hours=hours)

    @staticmethod
    def create_past_datetime(days: int = 1, hours: int = 0) -> datetime:
        """Create a past datetime"""
        return datetime.utcnow() - timedelta(days=days, hours=hours)


class DatabaseHelpers:
    """Helper functions for database operations in tests"""

    @staticmethod
    def create_test_club(db, **kwargs):
        """Create a test club in database"""

        defaults = {
            "name": fake.company(),
            "slug": "".join(random.choices(string.ascii_lowercase, k=10)),
            "email": fake.email(),
            "phone": fake.phone(),
        }
        defaults.update(kwargs)

        club = Club(**defaults)
        db.add(club)
        db.commit()
        db.refresh(club)
        return club

    @staticmethod
    def create_test_customer(db, club_id, **kwargs):
        """Create a test customer in database"""

        defaults = {
            "club_id": club_id,
            "name": fake.name(),
            "last_name": fake(),
            "phone": fake.phone(),
        }
        defaults.update(kwargs)

        customer = Customer(**defaults)
        db.add(customer)
        db.commit()
        db.refresh(customer)
        return customer

    @staticmethod
    def create_test_booking(db, club_id, customer_id, **kwargs):
        """Create a test booking in database"""

        start_time = datetime.utcnow() + timedelta(days=1)
        defaults = {
            "club_id": club_id,
            "customer_id": customer_id,
            "court_name": "Court 1",
            "start_time": start_time,
            "end_time": start_time + timedelta(hours=1),
            "status": "confirmed",
        }
        defaults.update(kwargs)

        booking = Booking(**defaults)
        db.add(booking)
        db.commit()
        db.refresh(booking)
        return booking

    @staticmethod
    def create_test_user(db, club_id=None, **kwargs):
        """Create a test user in database"""

        pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

        defaults = {
            "email": fake.email(),
            "username": fake.user_name(),
            "hashed_password": pwd_context.hash("testpassword123"),
            "full_name": fake.name(),
            "role": "club_admin",
            "is_active": True,
        }

        if club_id:
            defaults["club_id"] = club_id

        defaults.update(kwargs)

        user = User(**defaults)
        db.add(user)
        db.commit()
        db.refresh(user)
        return user

    @staticmethod
    def cleanup_test_data(db):
        """Clean up test data from database"""
        # Order matters due to foreign keys
        try:
            db.query(Notification).delete()
            db.query(Conversation).delete()
            db.query(Booking).delete()
            db.query(Customer).delete()
            db.query(User).delete()
            db.query(Club).delete()
            db.commit()
        except Exception as e:
            db.rollback()
            print(f"Cleanup error: {e}")


class AssertionHelpers:
    """Custom assertions for common test scenarios"""

    @staticmethod
    def assert_booking_valid(booking_data: Dict):
        """Assert booking data has valid structure"""
        required_fields = [
            "id",
            "club_id",
            "customer_id",
            "court_name",
            "start_time",
            "end_time",
        ]
        for field in required_fields:
            assert field in booking_data, f"Missing required field: {field}"

        # Validate datetime fields
        start = datetime.fromisoformat(booking_data["start_time"].replace("Z", "+00:00"))
        end = datetime.fromisoformat(booking_data["end_time"].replace("Z", "+00:00"))
        assert end > start, "End time must be after start time"

    @staticmethod
    def assert_customer_valid(customer_data: Dict):
        """Assert customer data has valid structure"""
        required_fields = ["id", "club_id", "first_name", "last_name", "phone_number"]
        for field in required_fields:
            assert field in customer_data, f"Missing required field: {field}"

        # Phone number should start with +
        if customer_data.get("phone_number"):
            assert customer_data["phone_number"].startswith("+"), "Phone number should start with +"

    @staticmethod
    def assert_club_valid(club_data: Dict):
        """Assert club data has valid structure"""
        required_fields = ["id", "name", "slug", "email"]
        for field in required_fields:
            assert field in club_data, f"Missing required field: {field}"

    @staticmethod
    def assert_notification_valid(notification_data: Dict):
        """Assert notification data has valid structure"""
        required_fields = ["id", "club_id", "notification_type", "recipient", "message"]
        for field in required_fields:
            assert field in notification_data, f"Missing required field: {field}"

        # Validate notification type
        assert notification_data["notification_type"] in [
            "sms",
            "email",
            "push",
        ], f"Invalid notification type: {notification_data['notification_type']}"


class MockHelpers:
    """Helpers for creating mocks"""

    @staticmethod
    def mock_vapi_response(call_id: str = "test_call_123", status: str = "success"):
        """Create mock VAPI API response"""
        return {
            "call_id": call_id,
            "status": status,
            "assistant_id": "asst_test_123",
            "created_at": datetime.utcnow().isoformat(),
        }

    @staticmethod
    def mock_twilio_response(message_sid: str = "SM123456", status: str = "sent"):
        """Create mock Twilio response"""
        return {
            "sid": message_sid,
            "status": status,
            "to": "+46701234567",
            "from": "+46709999999",
            "body": "Test message",
        }

    @staticmethod
    def mock_matchi_slots_response(date: str = None):
        """Create mock Matchi available slots response"""
        if not date:
            date = (datetime.utcnow() + timedelta(days=1)).strftime("%Y-%m-%d")

        return {
            "date": date,
            "slots": [
                {"court": "Court 1", "time": "10:00", "available": True, "price": 200},
                {"court": "Court 1", "time": "11:00", "available": True, "price": 200},
                {"court": "Court 2", "time": "14:00", "available": True, "price": 250},
            ],
        }

    @staticmethod
    def mock_knowledge_base_response(query: str):
        """Create mock knowledge base query response"""
        return {
            "query": query,
            "results": [
                {
                    "content": "Tennis courts are available from 9 AM to 9 PM",
                    "score": 0.95,
                    "metadata": {"source": "club_info"},
                },
                {
                    "content": "Membership includes 4 free court hours per month",
                    "score": 0.87,
                    "metadata": {"source": "membership_info"},
                },
            ],
        }


class ComparisonHelpers:
    """Helpers for comparing complex objects"""

    @staticmethod
    def compare_datetimes(dt1: datetime, dt2: datetime, tolerance_seconds: int = 5) -> bool:
        """Compare two datetimes with tolerance"""
        diff = abs((dt1 - dt2).total_seconds())
        return diff <= tolerance_seconds

    @staticmethod
    def compare_dicts_partial(dict1: Dict, dict2: Dict, keys: List[str]) -> bool:
        """Compare specific keys in two dictionaries"""
        for key in keys:
            if dict1.get(key) != dict2.get(key):
                return False
        return True

    @staticmethod
    def sanitize_for_comparison(data: Dict, remove_keys: List[str] = None) -> Dict:
        """Remove specified keys for comparison"""
        if remove_keys is None:
            remove_keys = ["id", "created_at", "updated_at"]

        sanitized = data.copy()
        for key in remove_keys:
            sanitized.pop(key, None)

        return sanitized


# Export commonly used functions at module level
generate_club = TestDataGenerator.generate_club_data
generate_customer = TestDataGenerator.generate_customer_data
generate_booking = TestDataGenerator.generate_booking_data
create_test_club = DatabaseHelpers.create_test_club
create_test_customer = DatabaseHelpers.create_test_customer
create_test_booking = DatabaseHelpers.create_test_booking
assert_valid = AssertionHelpers.assert_booking_valid
