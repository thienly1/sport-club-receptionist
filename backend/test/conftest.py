"""
Pytest Configuration and Fixtures
"""

from datetime import datetime, timedelta
from pathlib import Path
from typing import Generator
from unittest.mock import AsyncMock
from uuid import uuid4

import jwt
import pytest
from fastapi.testclient import TestClient
from passlib.context import CryptContext
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

# Import config module with alias to avoid conflict with FastAPI app
import app.config as app_config
from app.config import settings
from app.database import get_db
from app.main import app  # This is the FastAPI instance
from app.models.booking import Booking, BookingStatus, BookingType
from app.models.club import Club
from app.models.conversation import Conversation
from app.models.customer import Customer
from app.models.notification import Notification
from app.models.user import User

# Set the path to .env file
BASE_DIR = Path(__file__).parent.parent
env_path = BASE_DIR / "src" / ".env"

app_config.Settings.Config.env_file = str(env_path)
# Recreate settings
app_config.settings = app_config.Settings()

# Rest of the file stays the same...

# Use same database - tests will clean up after themselves
SQLALCHEMY_TEST_DATABASE_URL = settings.DATABASE_URL
print(f"Using test database URL: {SQLALCHEMY_TEST_DATABASE_URL}")

# Test database configuration
engine = create_engine(settings.DATABASE_URL)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(scope="function")
def db() -> Generator[Session, None, None]:
    """Use existing database, only clean up test data after each test"""
    # Assume tables already exist - don't create/drop them
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        # Rollback any pending transactions
        db.rollback()

        # Clean up test data only (delete in order to respect foreign keys)
        try:
            db.query(Notification).delete()
            db.query(Booking).delete()
            db.query(Conversation).delete()
            db.query(Customer).delete()
            db.query(User).delete()
            db.query(Club).delete()
            db.commit()
        except Exception as e:
            db.rollback()
            print(f"Cleanup error: {e}")
        finally:
            db.close()


@pytest.fixture(scope="function")
def client(db: Session) -> Generator[TestClient, None, None]:
    """Create a test client with database override"""

    def override_get_db():
        try:
            yield db
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db

    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.clear()


@pytest.fixture
def test_club(db: Session) -> Club:
    """Create a test club"""
    unique_id = str(uuid4())[:8]

    club = Club(
        name="Test Tennis Club",
        slug=f"test-tennis-club-{unique_id}",  # Make unique
        email=f"test-{unique_id}@tennisclub.com",  # Make unique
        phone="+46701234567",
        address="Test Street 123",
        city="Stockholm",
        postal_code="11122",
        country="Sweden",
        description="A test tennis club",
        website="https://testtennisclub.com",
        membership_types=[
            {"name": "Individual", "price": 2000, "currency": "SEK", "period": "year"},
            {"name": "Family", "price": 3500, "currency": "SEK", "period": "year"},
        ],
        pricing_info={
            "court_rental": {
                "indoor": 200,
                "outdoor": 150,
                "currency": "SEK",
                "unit": "hour",
            }
        },
        facilities=["Indoor courts", "Outdoor courts", "Cafe"],
        opening_hours={
            "monday": {"open": "06:00", "close": "22:00"},
            "tuesday": {"open": "06:00", "close": "22:00"},
        },
        is_active=True,
        subscription_tier="premium",
    )
    db.add(club)
    db.commit()
    db.refresh(club)
    return club


@pytest.fixture
def test_user(db: Session, test_club: Club) -> User:
    """Create a test user"""
    pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
    unique_id = str(uuid4())[:8]
    user = User(
        email=f"testuser-{unique_id}@example.com",
        username=f"testuser-{unique_id}",
        hashed_password=pwd_context.hash("testpassword123"),
        full_name="Test User",
        role="super_admin",
        is_active=True,
        club_id=test_club.id,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@pytest.fixture
def test_club_admin(db: Session, test_club: Club) -> User:
    """Create a test club admin user"""
    pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

    unique_id = str(uuid4())[:8]
    user = User(
        email=f"clubadmin-{unique_id}@example.com",
        username=f"clubadmin-{unique_id}",
        hashed_password=pwd_context.hash("adminpassword123"),
        full_name="Club Admin",
        role="club_admin",
        is_active=True,
        club_id=test_club.id,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@pytest.fixture
def test_customer(db: Session, test_club: Club) -> Customer:
    """Create a test customer"""
    customer = Customer(
        club_id=test_club.id,
        phone="+46709876543",
        name="John Doe",
        email="john.doe@example.com",
        status="lead",
        notes="Test customer for testing purposes",
    )
    db.add(customer)
    db.commit()
    db.refresh(customer)
    return customer


@pytest.fixture
def test_booking(db: Session, test_club: Club, test_customer: Customer) -> Booking:
    """Create a test booking"""
    start_time = datetime.utcnow() + timedelta(days=1)

    booking = Booking(
        club_id=test_club.id,
        customer_id=test_customer.id,
        booking_type=BookingType.COURT,
        resource_name="Court 1",
        booking_date=start_time,
        start_time=start_time,
        end_time=start_time + timedelta(hours=1),
        status=BookingStatus.CONFIRMED,
        price=200.0,
        currency="SEK",
        contact_name="John Doe",
        contact_phone="+46709876543",
        contact_email="john.doe@example.com",
    )
    db.add(booking)
    db.commit()
    db.refresh(booking)
    return booking


@pytest.fixture
def test_conversation(db: Session, test_club: Club, test_customer: Customer) -> Conversation:
    """Create a test conversation"""
    # Add unique suffix to avoid conflicts
    unique_id = str(uuid4())[:8]

    conversation = Conversation(
        club_id=test_club.id,
        customer_id=test_customer.id,
        vapi_call_id=f"test_call_{unique_id}",  # Make unique
        phone_number=test_customer.phone,
        status="completed",
        call_duration=120,
        intent="booking_inquiry",
        sentiment="positive",
        summary="Customer inquired about court availability",
    )
    db.add(conversation)
    db.commit()
    db.refresh(conversation)
    return conversation


@pytest.fixture
def auth_headers(test_user: User) -> dict:
    """Create authentication headers with super_admin role for testing"""

    # Create access token
    access_token_expires = timedelta(minutes=30)
    expire = datetime.utcnow() + access_token_expires

    to_encode = {
        "sub": str(test_user.id),
        "exp": expire,
    }

    access_token = jwt.encode(to_encode, settings.SECRET_KEY, algorithm="HS256")

    # Optional: decode to verify
    try:
        decoded = jwt.decode(access_token, settings.SECRET_KEY, algorithms=["HS256"])
        print(f"Decoded token: {decoded}")
    except Exception as e:
        print(f"Token decode error: {e}")

    return {"Authorization": f"Bearer {access_token}"}


@pytest.fixture
def club_admin_headers(test_club_admin: User) -> dict:
    """Create authentication headers for club admin testing"""
    access_token_expires = timedelta(minutes=30)
    expire = datetime.utcnow() + access_token_expires

    to_encode = {
        "sub": str(test_club_admin.id),
        "exp": expire,
    }

    access_token = jwt.encode(to_encode, settings.SECRET_KEY, algorithm="HS256")
    return {"Authorization": f"Bearer {access_token}"}


@pytest.fixture
def mock_vapi_service(mocker):
    """Mock VAPI service for testing"""
    # Patch where VAPIService is imported/used, not where it's defined
    mock_service = mocker.patch("app.routes.club.VAPIService")
    mock_instance = mock_service.return_value

    # Mock async methods with AsyncMock
    mock_instance.create_assistant = AsyncMock(return_value={"success": True, "assistant_id": "test_assistant_123"})
    mock_instance.update_assistant = AsyncMock(return_value={"success": True})
    mock_instance.make_outbound_call = AsyncMock(return_value={"success": True, "call_id": "test_call_123"})

    return mock_instance


@pytest.fixture
def mock_notification_service(mocker):
    """Mock Notification service for testing"""
    mock_service = mocker.patch("app.routes.vapi.NotificationService")
    mock_instance = mock_service.return_value

    mock_instance.send_sms.return_value = {
        "success": True,
        "message_id": "test_msg_123",
    }

    mock_instance.send_email.return_value = {"success": True}

    mock_instance.create_notification.return_value = {
        "success": True,
        "notification_id": "test_notif_123",
    }

    mock_instance.send_escalation_to_manager.return_value = {
        "success": True,
        "notification_sent": True,
    }

    return mock_instance


@pytest.fixture
def mock_matchi_service(mocker):
    """Mock Matchi service for testing"""
    mock_service = mocker.patch("app.services.matchi_service.MatchiService")
    mock_instance = mock_service.return_value

    # Mock common methods
    mock_instance.get_available_slots.return_value = {
        "success": True,
        "slots": [
            {"time": "10:00", "court": "Court 1", "price": 200},
            {"time": "11:00", "court": "Court 1", "price": 200},
        ],
    }

    mock_instance.create_booking.return_value = {
        "success": True,
        "booking_id": "matchi_booking_123",
    }

    return mock_instance
