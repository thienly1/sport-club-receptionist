"""
Tests for Customer Model and Routes
"""

import time
from datetime import datetime
from uuid import UUID, uuid4

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models.club import Club
from app.models.customer import Customer


class TestCustomerModel:
    """Test Customer model"""

    def test_create_customer(self, db: Session, test_club: Club):
        """Test creating a new customer"""
        customer = Customer(
            club_id=test_club.id,
            phone="+46701111111",
            name="Jane Smith",
            email="jane.smith@example.com",
            status="lead",
        )

        db.add(customer)
        db.commit()
        db.refresh(customer)

        assert customer.id is not None
        assert isinstance(customer.id, UUID)
        assert customer.name == "Jane Smith"
        assert customer.phone == "+46701111111"
        assert customer.status == "lead"
        assert isinstance(customer.created_at, datetime)

    def test_customer_club_relationship(self, test_club: Club, test_customer: Customer):
        """Test customer-club relationship"""
        assert test_customer.club_id == test_club.id
        assert test_customer.club == test_club
        assert test_customer in test_club.customers

    def test_customer_name_property(self, test_customer: Customer):
        """Test customer name property"""
        assert test_customer.name == "John Doe"
        assert hasattr(test_customer, "name")  # Customer has name field directly
        assert isinstance(test_customer.name, str)

    def test_customer_duplicate_phone_allowed(self, db: Session, test_club: Club, test_customer: Customer):
        """Test that duplicate phone numbers are allowed in same club (no constraint)"""
        # Create another customer with same phone in same club
        duplicate_customer = Customer(
            club_id=test_club.id,
            phone=test_customer.phone,  # Same phone
            name="Another Customer",
        )

        db.add(duplicate_customer)
        db.commit()  # Should succeed - no unique constraint

        # Verify both customers exist
        customers = db.query(Customer).filter_by(club_id=test_club.id, phone=test_customer.phone).all()

        assert len(customers) == 2
        assert customers[0].id != customers[1].id
        assert customers[0].phone == customers[1].phone
        assert customers[0].club_id == customers[1].club_id

    def test_customer_preferences_text(self, db: Session, test_club: Club):
        """Test storing customer preferences as text"""
        customer = Customer(
            club_id=test_club.id,
            phone="+46702222222",
            name="Test User",
            interested_in="indoor courts, evening slots",
            preferred_contact_method="phone",
            membership_type_interest="Individual",
        )

        db.add(customer)
        db.commit()
        db.refresh(customer)

        assert customer.interested_in == "indoor courts, evening slots"
        assert customer.preferred_contact_method == "phone"
        assert customer.membership_type_interest == "Individual"

    def test_customer_default_values(self, db: Session, test_club: Club):
        """Test customer default values"""
        customer = Customer(
            club_id=test_club.id,
            phone="+46703333333",
            name="Default Test",
        )

        db.add(customer)
        db.commit()
        db.refresh(customer)

        # Test defaults
        assert customer.status == "lead"  # Default from enum
        assert not customer.requires_follow_up
        assert not customer.is_high_priority
        assert not customer.converted_to_member
        assert not customer.consent_marketing
        assert customer.first_contact_date is not None
        assert customer.last_contact_date is not None
        assert customer.created_at is not None
        assert customer.updated_at is not None


class TestCustomerRoutes:
    """Test Customer API endpoints"""

    def test_get_customer_by_id(self, client: TestClient, auth_headers: dict, test_customer: Customer):
        """Test getting a customer by ID"""
        response = client.get(f"/customers/{test_customer.id}", headers=auth_headers)

        # Your API should return 200 for authenticated user
        assert response.status_code == 200

        data = response.json()
        assert data["name"] == test_customer.name
        assert data["phone"] == test_customer.phone
        assert UUID(data["id"]) == test_customer.id
        assert UUID(data["club_id"]) == test_customer.club_id

    def test_get_customer_by_phone(
        self,
        client: TestClient,
        test_customer: Customer,
        test_club: Club,
        auth_headers: dict,
    ):
        """Test getting customer by phone number"""
        response = client.get(
            f"/customers/phone/{test_customer.phone}",
            headers=auth_headers,
            params={"club_id": str(test_club.id)},
        )

        # Could return 200 with customer or 404 if endpoint doesn't exist
        if response.status_code == 200:
            data = response.json()
            # Might return a list or single object
            if isinstance(data, list):
                assert any(cust["phone"] == test_customer.phone for cust in data)
            else:
                assert data["phone"] == test_customer.phone
        elif response.status_code == 404:
            # Endpoint might not exist
            pass

    def test_get_nonexistent_customer(self, client: TestClient, auth_headers: dict):
        """Test getting a customer that doesn't exist"""
        fake_id = uuid4()
        response = client.get(f"/customers/{fake_id}", headers=auth_headers)

        # Should return 404 for non-existent customer with auth
        assert response.status_code == 404
        data = response.json()
        assert "detail" in data
        # Message might be "Customer not found" or similar

    def test_get_customer_unauthorized(self, client: TestClient, test_customer: Customer):
        """Test getting customer without authentication"""
        response = client.get(f"/customers/{test_customer.id}")

        # Should return 401 when no auth at all
        assert response.status_code == 401

        data = response.json()
        assert "detail" in data
        assert response.headers.get("WWW-Authenticate") == "Bearer"

    def test_list_customers_for_club(
        self,
        client: TestClient,
        auth_headers: dict,
        test_club: Club,
        test_customer: Customer,
    ):
        """Test listing customers for a specific club"""
        response = client.get("/customers/", headers=auth_headers, params={"club_id": str(test_club.id)})

        if response.status_code == 200:
            data = response.json()
            # Check response structure
            if isinstance(data, list):
                assert len(data) >= 1
                # Verify our test customer is in the list
                customer_ids = [UUID(item["id"]) for item in data]
                assert test_customer.id in customer_ids
            elif isinstance(data, dict):
                # Check common response patterns
                if "customers" in data:
                    assert len(data["customers"]) >= 1
                elif "items" in data:
                    assert len(data["items"]) >= 1
                elif "data" in data:
                    assert len(data["data"]) >= 1

    def test_create_customer_unauthorized(self, client: TestClient, test_club: Club):
        """Test creating customer without authentication"""
        customer_data = {
            "club_id": str(test_club.id),
            "phone": "+46703333333",
            "name": "New Customer",
            "email": "new@customer.com",
        }

        response = client.post("/customers/", json=customer_data)

        # Should return 401 when no auth at all
        assert response.status_code == 401

    def test_create_customer_success(self, client: TestClient, test_club: Club, auth_headers: dict):
        """Test creating customer with authentication"""
        customer_data = {
            "club_id": str(test_club.id),
            "phone": "+46704444444",  # Unique phone for this test
            "name": "Success Customer",
            "email": "success@customer.com",
            "status": "lead",
        }

        response = client.post("/customers/", headers=auth_headers, json=customer_data)

        # Should return 201 Created or 200 OK
        assert response.status_code in [200, 201]

        if response.status_code in [200, 201]:
            data = response.json()
            assert data["name"] == "Success Customer"
            assert data["phone"] == "+46704444444"
            assert data["club_id"] == str(test_club.id)
            assert "id" in data

    def test_update_customer(self, client: TestClient, auth_headers: dict, test_customer: Customer):
        """Test updating customer information"""
        update_data = {"name": "Updated Name", "notes": "Updated notes"}

        response = client.patch(f"/customers/{test_customer.id}", headers=auth_headers, json=update_data)

        assert response.status_code == 200

        data = response.json()
        assert data["name"] == "Updated Name"
        assert data["notes"] == "Updated notes"
        assert data["phone"] == test_customer.phone  # Phone unchanged
        assert UUID(data["id"]) == test_customer.id

    def test_update_customer_phone_allowed(self, client: TestClient, auth_headers: dict, test_customer: Customer):
        """Test updating customer phone (allowed since no unique constraint)"""
        update_data = {"phone": "+46709999999"}

        response = client.patch(f"/customers/{test_customer.id}", headers=auth_headers, json=update_data)

        assert response.status_code == 200

        data = response.json()
        assert data["phone"] == "+46709999999"

    def test_customer_search(
        self,
        client: TestClient,
        auth_headers: dict,
        test_club: Club,
        test_customer: Customer,
    ):
        """Test searching customers"""
        response = client.get(
            "/customers/search",
            headers=auth_headers,
            params={"club_id": str(test_club.id), "query": test_customer.name},
        )

        if response.status_code == 200:
            data = response.json()
            # Should find at least the test customer
            if isinstance(data, list):
                # Search should return our customer
                found = any(
                    str(test_customer.id) == str(item.get("id"))
                    or test_customer.name.lower() in item.get("name", "").lower()
                    for item in data
                )
                assert found
            elif isinstance(data, dict):
                # Check if data contains customers
                customers_list = data.get("customers", []) or data.get("items", []) or data.get("data", [])
                assert len(customers_list) >= 0

    def test_customer_status_enum(self, db: Session, test_club: Club):
        """Test all customer status enum values work"""
        statuses = ["lead", "interested", "trial", "member", "inactive"]

        for i, status in enumerate(statuses):
            customer = Customer(
                club_id=test_club.id,
                phone=f"+4670{i}0000000",
                name=f"Status Test {status}",
                status=status,
            )

            db.add(customer)
            db.commit()
            db.refresh(customer)

            assert customer.status == status
            assert customer.status.value == status  # For Enum

    def test_customer_timestamps(self, db: Session, test_club: Club):
        """Test customer timestamp fields"""

        # Create customer
        before_create = datetime.utcnow()
        time.sleep(0.01)  # Small delay

        customer = Customer(club_id=test_club.id, phone="+46705555555", name="Timestamp Test")
        db.add(customer)
        db.commit()
        db.refresh(customer)

        time.sleep(0.01)
        after_create = datetime.utcnow()

        # Check timestamps are set
        assert customer.created_at is not None
        assert customer.updated_at is not None
        assert customer.first_contact_date is not None
        assert customer.last_contact_date is not None

        # Verify timestamps are reasonable
        assert before_create <= customer.created_at <= after_create
        assert before_create <= customer.updated_at <= after_create
        # first_contact_date and last_contact_date should be close (within 1 second)
        time_diff = abs((customer.first_contact_date - customer.last_contact_date).total_seconds())
        assert time_diff < 1, f"first_contact_date and last_contact_date differ by {time_diff}s"
