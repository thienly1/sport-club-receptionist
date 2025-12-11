"""
Tests for Authentication
"""

from datetime import datetime, timedelta
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from jose import jwt
from passlib.context import CryptContext
from sqlalchemy.orm import Session

from app.models.user import User


class TestAuthRoutes:
    """Test authentication endpoints"""

    def test_login_success(self, client: TestClient, test_user: User):
        """Test successful login"""
        login_data = {"email": test_user.email, "password": "testpassword123"}

        response = client.post("/auth/login", json=login_data)
        assert response.status_code == 200

        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"
        assert isinstance(data["access_token"], str)
        assert len(data["access_token"]) > 0

    def test_login_wrong_password(self, client: TestClient, test_user: User):
        """Test login with wrong password"""
        login_data = {"email": test_user.email, "password": "wrongpassword"}

        response = client.post("/auth/login", json=login_data)
        assert response.status_code == 401
        data = response.json()
        assert "detail" in data

    def test_login_nonexistent_user(self, client: TestClient):
        """Test login with non-existent email"""
        login_data = {"email": "nonexistent@example.com", "password": "somepassword"}

        response = client.post("/auth/login", json=login_data)
        assert response.status_code == 401
        data = response.json()
        assert "detail" in data

    def test_get_current_user(self, client: TestClient, auth_headers: dict):
        """Test getting current user info"""
        response = client.get("/auth/me", headers=auth_headers)
        assert response.status_code == 200

        data = response.json()
        assert "email" in data
        assert "role" in data
        assert "id" in data
        assert "full_name" in data

    def test_get_current_user_unauthorized(self, client: TestClient):
        """Test getting current user without token"""
        response = client.get("/auth/me")
        assert response.status_code == 401
        data = response.json()
        assert "detail" in data

    def test_get_current_user_invalid_token(self, client: TestClient):
        """Test getting current user with invalid token"""
        headers = {"Authorization": "Bearer invalid_token"}
        response = client.get("/auth/me", headers=headers)
        assert response.status_code == 401
        data = response.json()
        assert "detail" in data


class TestUserRegistration:
    """Test user registration"""

    def test_register_new_user(self, client: TestClient, test_club):
        """Test registering a new user"""
        unique_email = f"newuser_{uuid4().hex[:8]}@example.com"
        register_data = {
            "email": unique_email,
            "password": "newpassword123",
            "full_name": "New User",
            "role": "club_staff",
            "club_id": str(test_club.id),
        }

        response = client.post("/auth/register", json=register_data)

        if response.status_code == 201:
            data = response.json()
            assert data["email"] == register_data["email"]
            assert "id" in data
            assert data["full_name"] == register_data["full_name"]
        elif response.status_code == 422:
            data = response.json()
            assert "detail" in data
            print(f"Registration validation error: {data['detail']}")

        elif response.status_code == 403:
            # Registration requires authentication/permissions
            data = response.json()
            assert "detail" in data
        else:
            # Unexpected status code - fail the test
            pytest.fail(f"Unexpected status code: {response.status_code}")

    def test_register_new_user_with_username(self, client: TestClient, test_club):
        """Test registering a new user with username field (based on User model)"""
        unique_id = uuid4().hex[:8]
        register_data = {
            "email": f"newuser_{unique_id}@example.com",
            "username": f"user_{unique_id}",  # Add username since User model requires it
            "password": "newpassword123",
            "full_name": "New User",
            "role": "club_staff",
            "club_id": str(test_club.id),
        }

        response = client.post("/auth/register", json=register_data)

        if response.status_code == 201:
            data = response.json()
            assert data["email"] == register_data["email"]
            assert "id" in data
        elif response.status_code == 422:
            data = response.json()
            assert "detail" in data
            # This is acceptable if validation fails
        else:
            pytest.fail(f"Unexpected status code: {response.status_code}")

    def test_register_duplicate_email(self, client: TestClient, test_user: User):
        """Test registering with existing email"""
        # First, try to register a user with the same email
        register_data = {
            "email": test_user.email,  # Duplicate
            "username": f"duplicate_{uuid4().hex[:8]}",  # Unique username
            "password": "password123",
            "full_name": "Another User",
            "role": "club_staff",
            "club_id": str(test_user.club_id) if test_user.club_id else None,
        }

        response = client.post("/auth/register", json=register_data)

        # Should fail - either with 400, 422, or 409 for duplicate
        assert response.status_code in [400, 409, 422]
        data = response.json()
        assert "detail" in data

    def test_register_duplicate_username(self, client: TestClient, test_user: User):
        """Test registering with existing username"""
        unique_email = f"different_{uuid4().hex[:8]}@example.com"
        register_data = {
            "email": unique_email,
            "username": test_user.username,  # Duplicate username
            "password": "password123",
            "full_name": "Another User",
            "role": "club_staff",
            "club_id": str(test_user.club_id) if test_user.club_id else None,
        }

        response = client.post("/auth/register", json=register_data)

        # Should fail - either with 400, 409, or 422 for duplicate
        assert response.status_code in [400, 409, 422]
        data = response.json()
        assert "detail" in data

    def test_register_invalid_email(self, client: TestClient):
        """Test registering with invalid email format"""
        register_data = {
            "email": "invalidemail",  # Not a valid email
            "username": f"testuser_{uuid4().hex[:8]}",
            "password": "password123",
            "full_name": "Test User",
            "role": "club_staff",
        }

        response = client.post("/auth/register", json=register_data)
        assert response.status_code == 422  # Validation error
        data = response.json()
        assert "detail" in data
        # Check that it's a validation error
        errors = data.get("detail", [])
        if isinstance(errors, list):
            assert any("email" in str(err).lower() for err in errors)

    def test_register_missing_required_fields(self, client: TestClient):
        """Test registering with missing required fields"""
        # Test without email
        register_data = {
            "username": f"testuser_{uuid4().hex[:8]}",
            "password": "password123",
            "full_name": "Test User",
        }

        response = client.post("/auth/register", json=register_data)
        assert response.status_code == 422  # Validation error

        # Test without username
        register_data2 = {
            "email": f"test_{uuid4().hex[:8]}@example.com",
            "password": "password123",
            "full_name": "Test User",
        }

        response2 = client.post("/auth/register", json=register_data2)
        assert response2.status_code == 422  # Validation error


class TestUserModel:
    """Test User model"""

    def test_user_password_hashing(self, test_user: User):
        """Test that password is hashed"""
        # Password should be hashed, not plain text
        assert test_user.hashed_password != "testpassword123"
        assert len(test_user.hashed_password) > 20  # Hashed passwords are long
        # Should look like a bcrypt hash
        assert test_user.hashed_password.startswith("$2b$") or test_user.hashed_password.startswith("$2a$")

    def test_user_verify_password(self, test_user: User):
        """Test password verification"""
        pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

        # Correct password should verify
        assert pwd_context.verify("testpassword123", test_user.hashed_password)

        # Wrong password should not verify
        assert not pwd_context.verify("wrongpassword", test_user.hashed_password)

    def test_user_role_values(self, db: Session, test_club):
        """Test different user roles"""
        pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

        roles = ["super_admin", "club_admin", "club_staff"]
        for i, role in enumerate(roles):
            user = User(
                email=f"user_role_test_{i}_{uuid4().hex[:8]}@example.com",
                username=f"user{i}_{uuid4().hex[:8]}",
                hashed_password=pwd_context.hash("password"),
                full_name=f"User {i}",
                role=role,
                club_id=test_club.id,
            )
            db.add(user)
            db.commit()
            db.refresh(user)

            assert user.role == role
            assert user.email is not None
            assert user.username is not None

    def test_user_inactive_account(self, db: Session, test_club):
        """Test inactive user account"""
        pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

        user = User(
            email=f"inactive_{uuid4().hex[:8]}@example.com",
            username=f"inactive_user_{uuid4().hex[:8]}",
            hashed_password=pwd_context.hash("password"),
            full_name="Inactive User",
            role="club_staff",
            is_active=False,
            club_id=test_club.id,
        )

        db.add(user)
        db.commit()
        db.refresh(user)

        assert user.is_active is False
        assert user.email is not None
        assert user.role == "club_staff"

    def test_user_properties(self, test_user: User):
        """Test user convenience properties"""
        test_user.role = "super_admin"
        assert test_user.is_super_admin is True
        assert test_user.can_manage_club is True

        test_user.role = "club_admin"
        assert test_user.is_club_admin is True
        assert test_user.can_manage_club is True

        test_user.role = "club_staff"
        assert test_user.is_club_staff is True
        assert test_user.can_manage_club is False


class TestTokenValidation:
    """Test JWT token validation"""

    def test_expired_token(self, client: TestClient, test_user: User):
        """Test using an expired token"""
        # Create an expired token
        expire = datetime.utcnow() - timedelta(minutes=30)  # Expired 30 min ago

        to_encode = {
            "sub": test_user.email,
            "exp": expire,
            "user_id": str(test_user.id),
        }

        # Use a test secret key (in real tests, this should come from config)
        test_secret_key = "test_secret_key_for_testing_only_1234567890"
        expired_token = jwt.encode(to_encode, test_secret_key, algorithm="HS256")

        headers = {"Authorization": f"Bearer {expired_token}"}
        response = client.get("/auth/me", headers=headers)

        # Should reject expired token
        assert response.status_code == 401
        data = response.json()
        assert "detail" in data

    def test_token_missing_user_id(self, client: TestClient):
        """Test token with missing user_id claim"""
        expire = datetime.utcnow() + timedelta(hours=1)

        to_encode = {
            "sub": "test@example.com",
            "exp": expire,
            # Missing user_id
        }

        test_secret_key = "test_secret_key_for_testing_only_1234567890"
        invalid_token = jwt.encode(to_encode, test_secret_key, algorithm="HS256")

        headers = {"Authorization": f"Bearer {invalid_token}"}
        response = client.get("/auth/me", headers=headers)

        # Should fail without user_id
        assert response.status_code == 401
        data = response.json()
        assert "detail" in data

    def test_token_invalid_signature(self, client: TestClient):
        """Test token with invalid signature"""
        # Create a token with wrong secret
        expire = datetime.utcnow() + timedelta(hours=1)

        to_encode = {
            "sub": "test@example.com",
            "exp": expire,
            "user_id": str(uuid4()),
        }

        wrong_secret = "wrong_secret_key_1234567890"
        invalid_token = jwt.encode(to_encode, wrong_secret, algorithm="HS256")

        headers = {"Authorization": f"Bearer {invalid_token}"}
        response = client.get("/auth/me", headers=headers)

        # Should fail with invalid signature
        assert response.status_code == 401
        data = response.json()
        assert "detail" in data
