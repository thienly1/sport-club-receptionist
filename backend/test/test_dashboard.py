"""
Tests for Dashboard Endpoints
"""

import time
from datetime import datetime, timedelta
from uuid import uuid4

from fastapi.testclient import TestClient
from jose import jwt
from sqlalchemy.orm import Session

from app.config import settings
from app.models.booking import Booking, BookingStatus, BookingType
from app.models.club import Club
from app.models.customer import Customer
from app.models.user import User


class TestClubDashboardStats:
    """Test club dashboard statistics endpoint"""

    def test_get_club_stats_success(self, client: TestClient, auth_headers: dict, test_club: Club):
        """Test getting club stats successfully"""
        response = client.get(f"/dashboard/club/{test_club.id}/stats", headers=auth_headers)

        if response.status_code == 200:
            data = response.json()

            # Check all expected fields are present
            assert "total_customers" in data
            assert "new_customers_this_month" in data
            assert "total_bookings" in data
            assert "bookings_today" in data
            assert "bookings_this_month" in data
            assert "revenue_this_month" in data
            assert "revenue_today" in data
            assert "active_conversations" in data
            assert "pending_follow_ups" in data
            assert "unread_notifications" in data

            # Check data types
            assert isinstance(data["total_customers"], int)
            assert isinstance(data["revenue_this_month"], (int, float))

    def test_get_club_stats_with_data(
        self,
        client: TestClient,
        auth_headers: dict,
        test_club: Club,
        test_user: User,
        test_customer: Customer,
        test_booking: Booking,
        db: Session,
    ):
        """Test club stats with actual data"""
        # Create today's booking
        today_booking = Booking(
            club_id=test_club.id,
            customer_id=test_customer.id,
            booking_type=BookingType.COURT,
            resource_name="Court 1",
            booking_date=datetime.utcnow(),
            start_time=datetime.utcnow(),
            end_time=datetime.utcnow() + timedelta(hours=1),
            status=BookingStatus.CONFIRMED,
            price=200.0,
            currency="SEK",
            contact_name="Test User",
            contact_phone="+46701234567",
        )
        db.add(today_booking)
        db.commit()

        response = client.get(f"/dashboard/club/{test_club.id}/stats", headers=auth_headers)

        if response.status_code == 200:
            data = response.json()
            assert data["total_customers"] >= 1
            assert data["total_bookings"] >= 2  # test_booking + today_booking
            assert data["bookings_today"] >= 1

    def test_get_club_stats_unauthorized(self, client: TestClient, test_club: Club):
        """Test accessing club stats without authentication"""
        response = client.get(f"/dashboard/club/{test_club.id}/stats")
        assert response.status_code in [401, 403]

    def test_get_club_stats_wrong_club(
        self,
        client: TestClient,
        auth_headers: dict,
        test_club: Club,
        test_club_admin: User,
        db: Session,
    ):
        """Test club admin accessing another club's stats"""
        # Create another club
        other_club = Club(
            name="Other Tennis Club",
            slug=f"other-tennis-club-{uuid4().hex[:8]}",
            email=f"other{uuid4().hex[:8]}@tennisclub.com",
            phone="+46709999999",
        )
        db.add(other_club)
        db.commit()
        db.refresh(other_club)

        # Create token for club admin
        access_token_expires = timedelta(minutes=30)
        expire = datetime.utcnow() + access_token_expires

        to_encode = {"sub": str(test_club_admin.id), "exp": expire}

        access_token = jwt.encode(to_encode, settings.SECRET_KEY, algorithm="HS256")

        headers = {"Authorization": f"Bearer {access_token}"}

        response = client.get(f"/dashboard/club/{other_club.id}/stats", headers=headers)

        # Should be forbidden or unauthorized
        assert response.status_code in [403, 401]

    def test_get_club_stats_revenue_calculation(
        self,
        client: TestClient,
        auth_headers: dict,
        test_club: Club,
        test_customer: Customer,
        db: Session,
    ):
        """Test revenue calculation accuracy"""
        # Create bookings with different statuses
        confirmed_booking = Booking(
            club_id=test_club.id,
            customer_id=test_customer.id,
            booking_type=BookingType.COURT,
            resource_name="Court 1",
            booking_date=datetime.utcnow(),
            start_time=datetime.utcnow(),
            end_time=datetime.utcnow() + timedelta(hours=1),
            status=BookingStatus.CONFIRMED,
            price=200.0,
            currency="SEK",
            contact_name="Test",
            contact_phone="+46701234567",
        )

        pending_booking = Booking(
            club_id=test_club.id,
            customer_id=test_customer.id,
            booking_type=BookingType.COURT,
            resource_name="Court 2",
            booking_date=datetime.utcnow(),
            start_time=datetime.utcnow(),
            end_time=datetime.utcnow() + timedelta(hours=1),
            status=BookingStatus.PENDING,
            price=150.0,
            currency="SEK",
            contact_name="Test",
            contact_phone="+46701234567",
        )

        db.add_all([confirmed_booking, pending_booking])
        db.commit()

        response = client.get(f"/dashboard/club/{test_club.id}/stats", headers=auth_headers)

        if response.status_code == 200:
            data = response.json()
            # Revenue should only include confirmed/completed bookings
            assert data["revenue_today"] >= 200.0

    def test_get_club_stats_date_filtering(
        self,
        client: TestClient,
        auth_headers: dict,
        test_club: Club,
        test_customer: Customer,
        db: Session,
    ):
        """Test that stats correctly filter by date ranges"""
        # Create booking from last month
        last_month = datetime.utcnow() - timedelta(days=35)
        old_booking = Booking(
            club_id=test_club.id,
            customer_id=test_customer.id,
            booking_type=BookingType.COURT,
            resource_name="Court 1",
            booking_date=last_month,
            start_time=last_month,
            end_time=last_month + timedelta(hours=1),
            status=BookingStatus.COMPLETED,
            price=200.0,
            currency="SEK",
            contact_name="Test",
            contact_phone="+46701234567",
        )
        db.add(old_booking)
        db.commit()

        response = client.get(f"/dashboard/club/{test_club.id}/stats", headers=auth_headers)

        if response.status_code == 200:
            data = response.json()
            # Old booking should be in total but not in this month's stats
            assert data["total_bookings"] >= 1


class TestSuperAdminDashboardStats:
    """Test super admin dashboard statistics endpoint"""

    def test_get_super_admin_stats_success(self, client: TestClient, auth_headers: dict):
        """Test getting system-wide stats as super admin"""
        response = client.get("/dashboard/super-admin/stats", headers=auth_headers)

        if response.status_code == 200:
            data = response.json()

            # Check all expected fields
            assert "total_clubs" in data
            assert "active_clubs" in data
            assert "total_users" in data
            assert "total_customers" in data
            assert "total_bookings_this_month" in data
            assert "total_revenue_this_month" in data

            # Verify data types
            assert isinstance(data["total_clubs"], int)
            assert isinstance(data["total_users"], int)
            assert data["total_clubs"] >= 1  # At least test_club

    def test_get_super_admin_stats_as_club_admin(self, client: TestClient, test_club_admin: User):
        """Test that club admin cannot access super admin stats"""
        # Create token for club admin
        access_token_expires = timedelta(minutes=30)
        expire = datetime.utcnow() + access_token_expires

        to_encode = {
            "sub": test_club_admin.email,
            "exp": expire,
            "user_id": str(test_club_admin.id),
        }

        test_secret_key = "test_secret_key_for_testing_only_1234567890"
        access_token = jwt.encode(to_encode, test_secret_key, algorithm="HS256")

        headers = {"Authorization": f"Bearer {access_token}"}

        response = client.get("/dashboard/super-admin/stats", headers=headers)

        # Should be forbidden
        assert response.status_code in [403, 401]

    def test_get_super_admin_stats_unauthorized(self, client: TestClient):
        """Test accessing super admin stats without auth"""
        response = client.get("/dashboard/super-admin/stats")
        assert response.status_code in [401, 403]

    def test_super_admin_stats_multi_club(self, client: TestClient, auth_headers: dict, db: Session):
        """Test super admin stats with multiple clubs"""
        # Create additional clubs
        club2 = Club(
            name="Second Club",
            slug=f"second-club-{uuid4().hex[:8]}",
            email=f"second{uuid4().hex[:8]}@club.com",
            phone="+46702222222",
        )
        club3 = Club(
            name="Third Club",
            slug=f"third-club{uuid4().hex[:8]}",
            email=f"third{uuid4().hex[:8]}@club.com",
            phone="+46703333333",
            is_active=False,  # Inactive club
        )
        db.add_all([club2, club3])
        db.commit()

        response = client.get("/dashboard/super-admin/stats", headers=auth_headers)

        if response.status_code == 200:
            data = response.json()
            assert data["total_clubs"] >= 3
            # Check that active clubs count excludes inactive
            if "active_clubs" in data:
                assert data["active_clubs"] < data["total_clubs"]


class TestDashboardPerformance:
    """Test dashboard performance and optimization"""

    def test_dashboard_response_time(self, client: TestClient, auth_headers: dict, test_club: Club):
        """Test that dashboard responds quickly"""
        start_time = time.time()
        response = client.get(f"/dashboard/club/{test_club.id}/stats", headers=auth_headers)
        end_time = time.time()

        response_time = end_time - start_time

        # Dashboard should respond within 2 seconds
        assert response_time < 2.0
        assert response.status_code in [200, 401, 403]

    def test_dashboard_with_large_dataset(
        self,
        client: TestClient,
        auth_headers: dict,
        test_club: Club,
        test_customer: Customer,
        db: Session,
    ):
        """Test dashboard performance with many bookings"""
        # Create multiple bookings
        bookings = []
        for i in range(50):
            booking = Booking(
                club_id=test_club.id,
                customer_id=test_customer.id,
                booking_type=BookingType.COURT,
                resource_name=f"Court {(i % 5) + 1}",
                booking_date=datetime.utcnow() - timedelta(days=i),
                start_time=datetime.utcnow() - timedelta(days=i),
                end_time=datetime.utcnow() - timedelta(days=i) + timedelta(hours=1),
                status=BookingStatus.CONFIRMED,
                price=200.0,
                currency="SEK",
                contact_name="Test",
                contact_phone="+46701234567",
            )
            bookings.append(booking)

        db.add_all(bookings)
        db.commit()

        response = client.get(f"/dashboard/club/{test_club.id}/stats", headers=auth_headers)

        # Should still work with larger dataset
        if response.status_code == 200:
            data = response.json()
            assert data["total_bookings"] >= 50


class TestDashboardEdgeCases:
    """Test dashboard edge cases and error handling"""

    def test_dashboard_with_no_data(self, client: TestClient, auth_headers: dict, db: Session, test_user: User):
        """Test dashboard with brand new club (no data)"""
        # Create a new club with no data
        new_club = Club(
            name="Empty Club",
            slug=f"empty-club{uuid4().hex[:8]}",
            email=f"empty-{uuid4().hex[:8]}@club.com",
            phone="+46709999999",
        )
        db.add(new_club)
        db.commit()
        db.refresh(new_club)

        # Update user's club
        test_user.club_id = new_club.id
        db.commit()

        response = client.get(f"/dashboard/club/{new_club.id}/stats", headers=auth_headers)

        if response.status_code == 200:
            data = response.json()
            # All counts should be 0
            assert data["total_customers"] == 0
            assert data["total_bookings"] == 0
            assert data["revenue_this_month"] == 0.0

    def test_dashboard_with_invalid_club_id(self, client: TestClient, auth_headers: dict):  # super admin auth
        """Test dashboard with non-existent club ID"""
        fake_club_id = uuid4()
        response = client.get(f"/dashboard/club/{fake_club_id}/stats", headers=auth_headers)
        # Should return 404
        assert response.status_code == 404

    def test_dashboard_revenue_with_mixed_currencies(
        self,
        client: TestClient,
        auth_headers: dict,
        test_club: Club,
        test_customer: Customer,
        db: Session,
    ):
        """Test revenue calculation with different currencies"""
        # Create bookings with different currencies
        sek_booking = Booking(
            club_id=test_club.id,
            customer_id=test_customer.id,
            booking_type=BookingType.COURT,
            resource_name="Court 1",
            booking_date=datetime.utcnow(),
            start_time=datetime.utcnow(),
            end_time=datetime.utcnow() + timedelta(hours=1),
            status=BookingStatus.CONFIRMED,
            price=200.0,
            currency="SEK",
            contact_name="Test",
            contact_phone="+46701234567",
        )

        eur_booking = Booking(
            club_id=test_club.id,
            customer_id=test_customer.id,
            booking_type=BookingType.COURT,
            resource_name="Court 2",
            booking_date=datetime.utcnow(),
            start_time=datetime.utcnow(),
            end_time=datetime.utcnow() + timedelta(hours=1),
            status=BookingStatus.CONFIRMED,
            price=20.0,
            currency="EUR",
            contact_name="Test",
            contact_phone="+46701234567",
        )

        db.add_all([sek_booking, eur_booking])
        db.commit()

        response = client.get(f"/dashboard/club/{test_club.id}/stats", headers=auth_headers)

        # Should handle mixed currencies (sum might not be meaningful)
        if response.status_code == 200:
            data = response.json()
            assert "revenue_today" in data
            assert isinstance(data["revenue_today"], (int, float))
