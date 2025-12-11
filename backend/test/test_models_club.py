"""
Tests for Club Model
"""

from datetime import datetime
from uuid import UUID, uuid4

import pytest
from sqlalchemy.orm import Session

from app.models.club import Club
from app.models.customer import Customer


class TestClubModel:
    """Test Club model CRUD operations and relationships"""

    def test_create_club(self, db: Session):
        """Test creating a new club"""
        club = Club(
            name="New Tennis Club",
            slug=f"new-tennis-club-{uuid4().hex[:8]}",
            email=f"new-{uuid4().hex[:8]}@tennisclub.com",
            phone="+46701111111",
            address="New Street 1",
            city="Gothenburg",
            postal_code="41115",
            country="Sweden",
        )

        db.add(club)
        db.commit()
        db.refresh(club)

        assert club.id is not None
        assert isinstance(club.id, UUID)
        assert club.name == "New Tennis Club"
        assert club.is_active is True
        assert club.subscription_tier == "basic"
        assert isinstance(club.created_at, datetime)

    def test_club_unique_slug(self, db: Session, test_club: Club):
        """Test that club slug must be unique"""
        duplicate_club = Club(
            name="Another Club",
            slug=test_club.slug,  # Same slug
            email="another@example.com",
            phone="+46702222222",
        )

        db.add(duplicate_club)

        with pytest.raises(Exception):  # Will raise IntegrityError
            db.commit()

    def test_club_unique_email(self, db: Session, test_club: Club):
        """Test that club email must be unique"""
        duplicate_club = Club(
            name="Another Club",
            slug="another-club",
            email=test_club.email,  # Same email
            phone="+46702222222",
        )

        db.add(duplicate_club)

        with pytest.raises(Exception):  # Will raise IntegrityError
            db.commit()

    def test_club_json_fields(self, db: Session):
        """Test JSON fields in club model"""
        club = Club(
            name="JSON Test Club",
            slug=f"json-test-club-{uuid4().hex[:8]}",
            email=f"json-{uuid4().hex[:8]}@example.com",
            phone="+46703333333",
            membership_types=[
                {
                    "name": "Individual",
                    "price": 2000,
                    "currency": "SEK",
                    "period": "year",
                },
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
            facilities=["Indoor courts", "Outdoor courts", "Pro shop"],
            opening_hours={
                "monday": {"open": "06:00", "close": "22:00"},
                "tuesday": {"open": "07:00", "close": "21:00"},
            },
        )

        db.add(club)
        db.commit()
        db.refresh(club)

        assert len(club.membership_types) == 2
        assert club.membership_types[0]["name"] == "Individual"
        assert club.pricing_info["court_rental"]["indoor"] == 200
        assert "Indoor courts" in club.facilities
        assert club.opening_hours["monday"]["open"] == "06:00"

    def test_club_relationships(self, test_club: Club, test_customer: Customer):
        """Test club relationships"""
        # test_customer fixture creates a customer linked to test_club
        assert len(test_club.customers) == 1
        assert test_club.customers[0].name == "John Doe"

    def test_club_soft_delete(self, db: Session, test_club: Club):
        """Test soft delete functionality"""
        assert test_club.is_active is True

        # Soft delete
        test_club.is_active = False
        db.commit()
        db.refresh(test_club)

        assert test_club.is_active is False
        assert test_club.id is not None  # Record still exists

    def test_club_repr(self, test_club: Club):
        """Test string representation"""
        repr_str = repr(test_club)
        assert "Test Tennis Club" in repr_str
        assert "test-tennis-club" in repr_str

    def test_club_update(self, db: Session, test_club: Club):
        """Test updating club information"""
        original_name = test_club.name
        test_club.name = "Updated Tennis Club"
        test_club.description = "Updated description"

        db.commit()
        db.refresh(test_club)

        assert test_club.name == "Updated Tennis Club"
        assert test_club.name != original_name
        assert test_club.description == "Updated description"
        assert test_club.updated_at > test_club.created_at
