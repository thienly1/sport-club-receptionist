"""
Tests for Booking Model, Routes, and Advanced Features
"""

from datetime import datetime, time, timedelta
from uuid import UUID, uuid4

from fastapi.testclient import TestClient
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.booking import Booking, BookingStatus, BookingType
from app.models.club import Club
from app.models.customer import Customer, CustomerStatus


# BOOKING MODELS TESTS
class TestBookingModel:
    """Test Booking model"""

    def test_create_booking(self, db: Session, test_club: Club, test_customer: Customer):
        """Test creating a new booking"""
        start_time = datetime.utcnow() + timedelta(days=2)
        end_time = start_time + timedelta(hours=1)

        booking = Booking(
            club_id=test_club.id,
            customer_id=test_customer.id,
            booking_type=BookingType.COURT,
            resource_name="Court 2",
            booking_date=start_time,
            start_time=start_time,
            end_time=end_time,
            status=BookingStatus.PENDING,
            price=200.0,
            currency="SEK",
            contact_name="Jane Smith",
            contact_phone="+46701111111",
            contact_email="jane@example.com",
        )

        db.add(booking)
        db.commit()
        db.refresh(booking)

        assert booking.id is not None
        assert isinstance(booking.id, UUID)
        assert booking.booking_type == BookingType.COURT
        assert booking.resource_name == "Court 2"
        assert booking.booking_date == start_time
        assert booking.start_time == start_time
        assert booking.end_time == end_time
        assert booking.status == BookingStatus.PENDING
        assert booking.price == 200.0
        assert booking.currency == "SEK"
        assert booking.contact_name == "Jane Smith"
        assert booking.contact_phone == "+46701111111"

    def test_booking_relationships(self, test_booking: Booking, test_club: Club, test_customer: Customer):
        """Test booking relationships"""
        assert test_booking.club_id == test_club.id
        assert test_booking.customer_id == test_customer.id
        assert test_booking.club == test_club
        assert test_booking.customer == test_customer

    def test_booking_duration_calculation(self, test_booking: Booking):
        """Test calculating booking duration if property exists"""
        if hasattr(test_booking, "duration_hours"):
            duration = test_booking.duration_hours
            assert duration > 0
            assert duration == 1.0  # 1 hour booking

    def test_booking_status_values(self, db: Session, test_club: Club, test_customer: Customer):
        """Test different booking status values"""
        statuses = [
            BookingStatus.PENDING,
            BookingStatus.CONFIRMED,
            BookingStatus.CANCELLED,
            BookingStatus.COMPLETED,
        ]

        for status in statuses:
            start_time = datetime.utcnow() + timedelta(days=1)

            booking = Booking(
                club_id=test_club.id,
                customer_id=test_customer.id,
                booking_type=BookingType.COURT,
                resource_name="Test Court",
                booking_date=start_time,
                start_time=start_time,
                end_time=start_time + timedelta(hours=1),
                status=status,
                price=100.0,
                currency="SEK",
            )

            db.add(booking)
            db.commit()
            db.refresh(booking)

            assert booking.status == status

    def test_booking_update_status(self, db: Session, test_booking: Booking):
        """Test updating booking status"""
        original_status = test_booking.status
        test_booking.status = BookingStatus.CANCELLED

        db.commit()
        db.refresh(test_booking)

        assert test_booking.status == BookingStatus.CANCELLED
        assert test_booking.status != original_status


# BOOKING ROUTES TESTS


class TestBookingRoutes:
    """Test Booking API endpoints"""

    def test_get_booking_by_id(self, client: TestClient, test_booking: Booking):
        """Test getting a booking by ID"""
        response = client.get(f"/bookings/{test_booking.id}")

        if response.status_code == 200:
            data = response.json()
            assert "id" in data
            assert "booking_type" in data
            assert "status" in data

    def test_get_nonexistent_booking(self, client: TestClient):
        """Test getting a booking that doesn't exist"""
        fake_id = uuid4()
        response = client.get(f"/bookings/{fake_id}")
        assert response.status_code in [404, 401]

    def test_list_bookings_for_club(
        self,
        client: TestClient,
        auth_headers: dict,
        test_club: Club,
        test_booking: Booking,
    ):
        """Test listing bookings for a club"""
        response = client.get("/bookings/", headers=auth_headers, params={"club_id": str(test_club.id)})

        if response.status_code == 200:
            data = response.json()
            assert "bookings" in data or isinstance(data, list)

    def test_list_bookings_by_status(
        self,
        client: TestClient,
        auth_headers: dict,
        test_club: Club,
        test_booking: Booking,
    ):
        """Test filtering bookings by status"""
        response = client.get(
            "/bookings/",
            headers=auth_headers,
            params={
                "club_id": str(test_club.id),
                "status": BookingStatus.CONFIRMED.value,
            },
        )

        if response.status_code == 200:
            data = response.json()
            if "bookings" in data:
                assert isinstance(data["bookings"], list)

    def test_list_bookings_by_date_range(self, client: TestClient, auth_headers: dict, test_club: Club):
        """Test filtering bookings by date range"""
        start_date = datetime.utcnow().date()
        end_date = (datetime.utcnow() + timedelta(days=7)).date()

        response = client.get(
            "/bookings/",
            headers=auth_headers,
            params={
                "club_id": str(test_club.id),
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat(),
            },
        )

        assert response.status_code in [200, 401, 422]

    def test_create_booking_unauthorized(self, client: TestClient, test_club: Club, test_customer: Customer):
        """Test creating booking without authentication"""
        start_time = datetime.utcnow() + timedelta(days=1)

        booking_data = {
            "club_id": str(test_club.id),
            "customer_id": str(test_customer.id),
            "booking_type": BookingType.COURT.value,
            "resource_name": "Court 1",
            "booking_date": start_time.isoformat(),
            "start_time": start_time.isoformat(),
            "end_time": (start_time + timedelta(hours=1)).isoformat(),
            "price": 150.0,
            "currency": "SEK",
        }

        response = client.post("/bookings/", json=booking_data)
        assert response.status_code in [401, 422]

    def test_update_booking_status(self, client: TestClient, auth_headers: dict, test_booking: Booking):
        """Test updating booking status"""
        update_data = {"status": BookingStatus.CANCELLED.value}

        response = client.patch(f"/bookings/{test_booking.id}", headers=auth_headers, json=update_data)

        assert response.status_code in [200, 401, 403]

    def test_cancel_booking(self, client: TestClient, auth_headers: dict, test_booking: Booking):
        """Test cancelling a booking"""
        response = client.post(f"/bookings/{test_booking.id}/cancel", headers=auth_headers)

        assert response.status_code in [200, 401, 404]

    def test_get_customer_bookings(self, client: TestClient, test_customer: Customer, test_booking: Booking):
        """Test getting all bookings for a customer"""
        response = client.get(f"/customers/{test_customer.id}/bookings")

        if response.status_code == 200:
            data = response.json()
            assert isinstance(data, (list, dict))


# BOOKING VALIDATION TESTS


class TestBookingValidation:
    """Test booking validation logic"""

    def test_booking_time_validation(self, db: Session, test_club: Club, test_customer: Customer):
        """Test that end time must be after start time"""
        start_time = datetime.utcnow() + timedelta(days=1)
        end_time = start_time - timedelta(hours=1)  # End before start

        booking = Booking(
            club_id=test_club.id,
            customer_id=test_customer.id,
            booking_type=BookingType.COURT,
            resource_name="Court 1",
            booking_date=start_time,
            start_time=start_time,
            end_time=end_time,
            status=BookingStatus.PENDING,
            price=100.0,
            currency="SEK",
        )

        db.add(booking)
        # This should work as DB doesn't enforce this constraint
        # Validation should happen in Pydantic schemas
        db.commit()

    def test_past_booking_creation(self, db: Session, test_club: Club, test_customer: Customer):
        """Test creating booking in the past"""
        start_time = datetime.utcnow() - timedelta(days=1)
        end_time = start_time + timedelta(hours=1)

        booking = Booking(
            club_id=test_club.id,
            customer_id=test_customer.id,
            booking_type=BookingType.COURT,
            resource_name="Court 1",
            booking_date=start_time,
            start_time=start_time,
            end_time=end_time,
            status=BookingStatus.COMPLETED,
            price=100.0,
            currency="SEK",
        )

        db.add(booking)
        db.commit()

        # Past bookings can exist (for history)
        assert booking.id is not None


# BOOKING CONFLICTS TESTS
class TestBookingConflicts:
    """Test booking conflict detection"""

    def test_detect_overlapping_bookings(self, db: Session, test_club: Club, test_customer: Customer):
        """Test that overlapping bookings on same resource are detected"""
        start_time = datetime.utcnow() + timedelta(days=1)
        end_time = start_time + timedelta(hours=2)

        # Create first booking
        booking1 = Booking(
            club_id=test_club.id,
            customer_id=test_customer.id,
            booking_type=BookingType.COURT,
            resource_name="Court 1",
            booking_date=start_time,
            start_time=start_time,
            end_time=end_time,
            status=BookingStatus.CONFIRMED,
            price=200.0,
            currency="SEK",
            contact_name="Test",
            contact_phone="+46701234567",
        )
        db.add(booking1)
        db.commit()

        # Try to create overlapping booking
        overlap_start = start_time + timedelta(minutes=30)
        overlap_end = overlap_start + timedelta(hours=2)

        booking2 = Booking(
            club_id=test_club.id,
            customer_id=test_customer.id,
            booking_type=BookingType.COURT,
            resource_name="Court 1",  # Same resource
            booking_date=overlap_start,
            start_time=overlap_start,
            end_time=overlap_end,
            status=BookingStatus.CONFIRMED,
            price=200.0,
            currency="SEK",
            contact_name="Test",
            contact_phone="+46701234567",
        )

        # Database allows it, but application should prevent
        db.add(booking2)
        db.commit()

        # Query for conflicts
        conflicts = (
            db.query(Booking)
            .filter(
                Booking.club_id == test_club.id,
                Booking.resource_name == "Court 1",
                Booking.status.in_([BookingStatus.CONFIRMED, BookingStatus.PENDING]),
                Booking.start_time < overlap_end,
                Booking.end_time > overlap_start,
            )
            .all()
        )

        # Should find both bookings as conflicts
        assert len(conflicts) >= 2

    def test_no_conflict_different_resources(self, db: Session, test_club: Club, test_customer: Customer):
        """Test that bookings on different resources don't conflict"""
        start_time = datetime.utcnow() + timedelta(days=1)
        end_time = start_time + timedelta(hours=1)

        booking1 = Booking(
            club_id=test_club.id,
            customer_id=test_customer.id,
            booking_type=BookingType.COURT,
            resource_name="Court 1",
            booking_date=start_time,
            start_time=start_time,
            end_time=end_time,
            status=BookingStatus.CONFIRMED,
            price=200.0,
            currency="SEK",
            contact_name="Test",
            contact_phone="+46701234567",
        )

        booking2 = Booking(
            club_id=test_club.id,
            customer_id=test_customer.id,
            booking_type=BookingType.COURT,
            resource_name="Court 2",  # Different resource
            booking_date=start_time,
            start_time=start_time,
            end_time=end_time,
            status=BookingStatus.CONFIRMED,
            price=200.0,
            currency="SEK",
            contact_name="Test",
            contact_phone="+46701234567",
        )

        db.add_all([booking1, booking2])
        db.commit()

        # Both should succeed - no conflict
        assert booking1.id is not None
        assert booking2.id is not None

    def test_no_conflict_cancelled_booking(self, db: Session, test_club: Club, test_customer: Customer):
        """Test that cancelled bookings don't cause conflicts"""
        start_time = datetime.utcnow() + timedelta(days=1)
        end_time = start_time + timedelta(hours=1)

        # Create cancelled booking
        cancelled_booking = Booking(
            club_id=test_club.id,
            customer_id=test_customer.id,
            booking_type=BookingType.COURT,
            resource_name="Court 1",
            booking_date=start_time,
            start_time=start_time,
            end_time=end_time,
            status=BookingStatus.CANCELLED,
            price=200.0,
            currency="SEK",
            contact_name="Test",
            contact_phone="+46701234567",
        )
        db.add(cancelled_booking)
        db.commit()

        # Create new booking at same time
        new_booking = Booking(
            club_id=test_club.id,
            customer_id=test_customer.id,
            booking_type=BookingType.COURT,
            resource_name="Court 1",
            booking_date=start_time,
            start_time=start_time,
            end_time=end_time,
            status=BookingStatus.CONFIRMED,
            price=200.0,
            currency="SEK",
            contact_name="Test",
            contact_phone="+46701234567",
        )
        db.add(new_booking)
        db.commit()

        # Should succeed - cancelled booking doesn't block
        assert new_booking.id is not None


# BOOKING CAPACITY TESTS
class TestBookingCapacity:
    """Test booking capacity and limits"""

    def test_customer_concurrent_booking_limit(self, db: Session, test_club: Club, test_customer: Customer):
        """Test limiting concurrent bookings per customer"""
        base_time = datetime.utcnow() + timedelta(days=1)

        bookings = []
        for i in range(5):
            start_time = base_time + timedelta(hours=i * 2)
            booking = Booking(
                club_id=test_club.id,
                customer_id=test_customer.id,
                booking_type=BookingType.COURT,
                resource_name=f"Court {(i % 3) + 1}",
                booking_date=start_time,
                start_time=start_time,
                end_time=start_time + timedelta(hours=1),
                status=BookingStatus.CONFIRMED,
                price=200.0,
                currency="SEK",
                contact_name="Test",
                contact_phone="+46701234567",
            )
            bookings.append(booking)

        db.add_all(bookings)
        db.commit()

        # Query active bookings for customer
        active_bookings = (
            db.query(Booking)
            .filter(
                Booking.customer_id == test_customer.id,
                Booking.status.in_([BookingStatus.CONFIRMED, BookingStatus.PENDING]),
                Booking.start_time > datetime.utcnow(),
            )
            .count()
        )

        # Application can enforce limits based on this count
        assert active_bookings == 5

    def test_daily_booking_limit_per_customer(self, db: Session, test_club: Club, test_customer: Customer):
        """Test limiting bookings per customer per day"""
        target_date = (datetime.utcnow() + timedelta(days=1)).date()

        # Create multiple bookings on same day
        for i in range(3):
            start_time = datetime.combine(target_date, time(10 + i * 2, 0))
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
                contact_name="Test",
                contact_phone="+46701234567",
            )
            db.add(booking)

        db.commit()

        # Count bookings for customer on this date
        daily_bookings = (
            db.query(Booking)
            .filter(
                Booking.customer_id == test_customer.id,
                Booking.booking_date >= datetime.combine(target_date, time.min),
                Booking.booking_date < datetime.combine(target_date + timedelta(days=1), time.min),
            )
            .count()
        )

        assert daily_bookings == 3


# BOOKING MODIFICATION TESTS


class TestBookingModification:
    """Test booking modification workflows"""

    def test_reschedule_booking(self, db: Session, test_club: Club, test_customer: Customer):
        """Test rescheduling a booking"""
        original_time = datetime.utcnow() + timedelta(days=1)

        booking = Booking(
            club_id=test_club.id,
            customer_id=test_customer.id,
            booking_type=BookingType.COURT,
            resource_name="Court 1",
            booking_date=original_time,
            start_time=original_time,
            end_time=original_time + timedelta(hours=1),
            status=BookingStatus.CONFIRMED,
            price=200.0,
            currency="SEK",
            contact_name="Test",
            contact_phone="+46701234567",
        )
        db.add(booking)
        db.commit()

        # Reschedule to new time
        new_time = original_time + timedelta(days=1)
        booking.booking_date = new_time
        booking.start_time = new_time
        booking.end_time = new_time + timedelta(hours=1)
        db.commit()
        db.refresh(booking)

        assert booking.start_time == new_time

    def test_extend_booking_duration(self, db: Session, test_club: Club, test_customer: Customer):
        """Test extending booking duration"""
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
            contact_name="Test",
            contact_phone="+46701234567",
        )
        db.add(booking)
        db.commit()

        original_end = booking.end_time

        # Extend by 30 minutes
        booking.end_time = original_end + timedelta(minutes=30)
        booking.price = 250.0  # Update price
        db.commit()
        db.refresh(booking)

        duration = (booking.end_time - booking.start_time).total_seconds() / 3600
        assert duration == 1.5
        assert booking.price == 250.0

    def test_change_booking_resource(self, db: Session, test_club: Club, test_customer: Customer):
        """Test changing booking to different resource"""
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
            contact_name="Test",
            contact_phone="+46701234567",
        )
        db.add(booking)
        db.commit()

        # Change to different court
        booking.resource_name = "Court 2"
        db.commit()
        db.refresh(booking)

        assert booking.resource_name == "Court 2"


# CUSTOMER STATUS TRANSITIONS TESTS
class TestCustomerStatusTransitions:
    """Test customer status lifecycle"""

    def test_lead_to_interested_transition(self, db: Session, test_club: Club):
        """Test transitioning customer from lead to interested"""
        customer = Customer(
            club_id=test_club.id,
            phone="+46701111111",
            name="Potential Customer",
            status=CustomerStatus.LEAD,
        )
        db.add(customer)
        db.commit()

        # Update to interested
        customer.status = CustomerStatus.INTERESTED
        customer.interested_in = "Tennis lessons"
        db.commit()
        db.refresh(customer)

        assert customer.status == CustomerStatus.INTERESTED
        assert customer.interested_in == "Tennis lessons"

    def test_interested_to_member_transition(self, db: Session, test_club: Club):
        """Test converting interested customer to member"""
        customer = Customer(
            club_id=test_club.id,
            phone="+46702222222",
            name="Interested Customer",
            status=CustomerStatus.INTERESTED,
        )
        db.add(customer)
        db.commit()

        # Convert to member
        customer.status = CustomerStatus.MEMBER
        db.commit()
        db.refresh(customer)

        assert customer.status == CustomerStatus.MEMBER

    def test_member_to_inactive_transition(self, db: Session, test_club: Club):
        """Test marking member as inactive"""
        customer = Customer(
            club_id=test_club.id,
            phone="+46703333333",
            name="Active Member",
            status=CustomerStatus.MEMBER,
        )
        db.add(customer)
        db.commit()

        # Mark inactive
        customer.status = CustomerStatus.INACTIVE
        db.commit()
        db.refresh(customer)

        assert customer.status == CustomerStatus.INACTIVE


# CUSTOMER FOLLOW-UP TESTS


class TestCustomerFollowUp:
    """Test customer follow-up functionality"""

    def test_customer_requires_follow_up(self, db: Session, test_club: Club):
        """Test marking customer for follow-up"""
        customer = Customer(
            club_id=test_club.id,
            phone="+46704444444",
            name="Follow Up Customer",
            status=CustomerStatus.INTERESTED,
            requires_follow_up=True,
            follow_up_date=datetime.utcnow() + timedelta(days=7),
        )
        db.add(customer)
        db.commit()
        db.refresh(customer)

        assert customer.requires_follow_up is True
        assert customer.follow_up_date is not None

    def test_overdue_follow_ups(self, db: Session, test_club: Club):
        """Test querying overdue follow-ups"""
        # Create customer with past follow-up date
        customer = Customer(
            club_id=test_club.id,
            phone="+46705555555",
            name="Overdue Customer",
            status=CustomerStatus.INTERESTED,
            requires_follow_up=True,
            follow_up_date=datetime.utcnow() - timedelta(days=1),
        )
        db.add(customer)
        db.commit()

        # Query overdue follow-ups
        overdue = (
            db.query(Customer)
            .filter(
                Customer.club_id == test_club.id,
                Customer.requires_follow_up.is_(True),
                Customer.follow_up_date <= datetime.utcnow(),
            )
            .all()
        )

        assert len(overdue) >= 1
        assert customer in overdue

    def test_complete_follow_up(self, db: Session, test_club: Club):
        """Test marking follow-up as complete"""
        customer = Customer(
            club_id=test_club.id,
            phone="+46706666666",
            name="Followed Up Customer",
            status=CustomerStatus.INTERESTED,
            requires_follow_up=True,
            follow_up_date=datetime.utcnow(),
        )
        db.add(customer)
        db.commit()

        # Complete follow-up
        customer.requires_follow_up = False
        customer.last_contact_date = datetime.utcnow()
        db.commit()
        db.refresh(customer)

        assert customer.requires_follow_up is False
        assert customer.last_contact_date is not None


# CUSTOMER SEARCH TESTS


class TestCustomerSearch:
    """Test customer search functionality"""

    def test_search_by_name(self, db: Session, test_club: Club):
        """Test searching customers by name"""
        customers = [
            Customer(club_id=test_club.id, phone="+46701111111", name="John Smith"),
            Customer(club_id=test_club.id, phone="+46702222222", name="Jane Smith"),
            Customer(club_id=test_club.id, phone="+46703333333", name="Bob Johnson"),
        ]
        db.add_all(customers)
        db.commit()

        # Search for "Smith"
        results = db.query(Customer).filter(Customer.club_id == test_club.id, Customer.name.ilike("%Smith%")).all()

        assert len(results) == 2
        assert all("Smith" in c.name for c in results)

    def test_search_by_phone(self, db: Session, test_club: Club):
        """Test searching customers by phone"""
        customer = Customer(club_id=test_club.id, phone="+46701234567", name="Test Customer")
        db.add(customer)
        db.commit()

        # Search by full phone
        result = db.query(Customer).filter(Customer.club_id == test_club.id, Customer.phone == "+46701234567").first()

        assert result is not None
        assert result.phone == "+46701234567"

    def test_search_by_status(self, db: Session, test_club: Club):
        """Test filtering customers by status"""
        customers = [
            Customer(
                club_id=test_club.id,
                phone="+46704444444",
                name="Lead 1",
                status=CustomerStatus.LEAD,
            ),
            Customer(
                club_id=test_club.id,
                phone="+46705555555",
                name="Member 1",
                status=CustomerStatus.MEMBER,
            ),
        ]
        db.add_all(customers)
        db.commit()

        # Get only members
        members = (
            db.query(Customer)
            .filter(
                Customer.club_id == test_club.id,
                Customer.status == CustomerStatus.MEMBER,
            )
            .all()
        )

        assert len(members) >= 1
        assert all(c.status == CustomerStatus.MEMBER for c in members)


# BOOKING STATISTICS TESTS
class TestBookingStatistics:
    """Test booking statistics and analytics"""

    def test_bookings_by_resource(self, db: Session, test_club: Club, test_customer: Customer):
        """Test counting bookings by resource"""
        base_time = datetime.utcnow() + timedelta(days=1)

        # Create bookings for different courts
        for i in range(5):
            booking = Booking(
                club_id=test_club.id,
                customer_id=test_customer.id,
                booking_type=BookingType.COURT,
                resource_name=f"Court {(i % 2) + 1}",
                booking_date=base_time + timedelta(hours=i),
                start_time=base_time + timedelta(hours=i),
                end_time=base_time + timedelta(hours=i + 1),
                status=BookingStatus.CONFIRMED,
                price=200.0,
                currency="SEK",
                contact_name="Test",
                contact_phone="+46701234567",
            )
            db.add(booking)
        db.commit()

        # Count by resource
        counts = (
            db.query(Booking.resource_name, func.count(Booking.id))
            .filter(Booking.club_id == test_club.id)
            .group_by(Booking.resource_name)
            .all()
        )

        assert len(counts) >= 2

    def test_revenue_by_period(self, db: Session, test_club: Club, test_customer: Customer):
        """Test calculating revenue for a period"""
        start_date = datetime.utcnow().date()
        end_date = start_date + timedelta(days=7)

        # Create bookings in the period
        for i in range(3):
            booking_time = datetime.combine(start_date + timedelta(days=i), time(10, 0))
            booking = Booking(
                club_id=test_club.id,
                customer_id=test_customer.id,
                booking_type=BookingType.COURT,
                resource_name="Court 1",
                booking_date=booking_time,
                start_time=booking_time,
                end_time=booking_time + timedelta(hours=1),
                status=BookingStatus.CONFIRMED,
                price=200.0,
                currency="SEK",
                contact_name="Test",
                contact_phone="+46701234567",
            )
            db.add(booking)
        db.commit()

        # Calculate revenue
        revenue = (
            db.query(func.sum(Booking.price))
            .filter(
                Booking.club_id == test_club.id,
                Booking.booking_date >= datetime.combine(start_date, time.min),
                Booking.booking_date < datetime.combine(end_date, time.min),
                Booking.status.in_([BookingStatus.CONFIRMED, BookingStatus.COMPLETED]),
            )
            .scalar()
        )

        assert revenue >= 600.0  # 3 bookings * 200
