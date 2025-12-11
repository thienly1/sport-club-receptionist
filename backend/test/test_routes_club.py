"""
Tests for Club API Routes
"""

from uuid import uuid4

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models.club import Club


class TestClubRoutes:
    """Test Club API endpoints"""

    def test_get_root(self, client: TestClient):
        """Test root endpoint"""
        response = client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert "name" in data
        assert "version" in data
        assert data["status"] == "running"

    def test_health_check(self, client: TestClient):
        """Test health check endpoint"""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "timestamp" in data

    def test_api_info(self, client: TestClient):
        """Test API info endpoint"""
        response = client.get("/api/info")
        assert response.status_code == 200
        data = response.json()
        assert "app_name" in data
        assert "features" in data
        assert "endpoints" in data

    def test_create_club_unauthorized(self, client: TestClient):
        """Test creating club without authentication"""
        club_data = {
            "name": "New Club",
            "slug": "new-club",
            "email": "new@club.com",
            "phone": "+46701234567",
        }

        response = client.post("/clubs/", json=club_data)
        assert response.status_code in [401, 403]  # Unauthorized or Forbidden

    def test_get_club_by_id(self, client: TestClient, test_club: Club):
        """Test getting a club by ID"""
        response = client.get(f"/clubs/{test_club.id}")
        assert response.status_code == 200

        data = response.json()
        assert data["name"] == test_club.name
        assert data["slug"] == test_club.slug
        assert data["email"] == test_club.email

    def test_get_club_by_slug(self, client: TestClient, test_club: Club):
        """Test getting a club by slug"""
        response = client.get(f"/clubs/slug/{test_club.slug}")
        assert response.status_code == 200

        data = response.json()
        assert data["name"] == test_club.name
        assert data["slug"] == test_club.slug

    def test_get_nonexistent_club(self, client: TestClient):
        """Test getting a club that doesn't exist"""
        fake_id = uuid4()
        response = client.get(f"/clubs/{fake_id}")
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()

    def test_get_club_by_invalid_slug(self, client: TestClient):
        """Test getting a club with invalid slug"""
        response = client.get("/clubs/slug/nonexistent-slug")
        assert response.status_code == 404


class TestClubRoutesWithAuth:
    """Test Club API endpoints with authentication"""

    def test_list_clubs_as_super_admin(self, client: TestClient, auth_headers: dict):
        """Test listing clubs as super admin"""
        response = client.get("/clubs/", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert "clubs" in data
        assert "total" in data
        assert data["total"] >= 1
        assert len(data["clubs"]) >= 1

    def test_list_clubs_pagination(self, client: TestClient, auth_headers: dict):
        """Test clubs list pagination"""
        response = client.get("/clubs/", headers=auth_headers, params={"skip": 0, "limit": 10})
        assert response.status_code == 200
        data = response.json()
        assert "page" in data
        assert "page_size" in data
        assert data["page_size"] == 10

    def test_list_clubs_active_only_filter(self, client: TestClient, auth_headers: dict, db: Session):
        """Test filtering only active clubs"""
        # Create an inactive club
        inactive_club = Club(
            name="Inactive Club",
            slug=f"inactive-club{uuid4().hex[:8]}",
            email=f"inactive{uuid4().hex[:8]}@club.com",
            phone="+46709999999",
            is_active=False,
        )
        db.add(inactive_club)
        db.commit()

        response = client.get("/clubs/", headers=auth_headers, params={"active_only": True})
        assert response.status_code == 200

        data = response.json()
        # Should only return active clubs
        if response.status_code == 200 and "clubs" in data:
            for club in data["clubs"]:
                assert club["is_active"] is True


class TestClubMutationRoutes:
    """Test Club creation, update, and deletion"""

    def test_update_club(self, client: TestClient, auth_headers: dict, test_club: Club):
        """Test updating club information"""
        update_data = {
            "name": "Updated Club Name",
            "description": "Updated description",
        }

        response = client.patch(f"/clubs/{test_club.id}", headers=auth_headers, json=update_data)

        assert response.status_code == 200

    def test_update_nonexistent_club(self, client: TestClient, auth_headers: dict):
        """Test updating a club that doesn't exist"""
        fake_id = uuid4()
        update_data = {"name": "Updated Name"}

        response = client.patch(f"/clubs/{fake_id}", headers=auth_headers, json=update_data)

        # Should return 404 not found
        assert response.status_code == 404

    def test_delete_club(self, client: TestClient, auth_headers: dict, test_club: Club):
        """Test soft deleting a club"""
        response = client.delete(f"/clubs/{test_club.id}", headers=auth_headers)

        # Should be 204 on successful deletion
        assert response.status_code == 204

    def test_delete_nonexistent_club(self, client: TestClient, auth_headers: dict):
        """Test deleting a club that doesn't exist"""
        fake_id = uuid4()
        response = client.delete(f"/clubs/{fake_id}", headers=auth_headers)

        assert response.status_code == 404


class TestClubAssistantSync:
    """Test VAPI assistant synchronization"""

    def test_sync_assistant(self, client: TestClient, test_club: Club, mock_vapi_service):
        """Test syncing VAPI assistant"""
        response = client.post(f"/clubs/{test_club.id}/sync-assistant")

        assert response.status_code == 200

    def test_sync_assistant_nonexistent_club(self, client: TestClient):
        """Test syncing assistant for nonexistent club"""
        fake_id = uuid4()
        response = client.post(f"/clubs/{fake_id}/sync-assistant")

        assert response.status_code == 404
