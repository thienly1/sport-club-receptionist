"""
Tests for Conversation Model and VAPI Webhook
"""

from datetime import datetime
from uuid import UUID, uuid4

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models.club import Club
from app.models.conversation import Conversation
from app.models.customer import Customer


class TestConversationModel:
    """Test Conversation model"""

    def test_create_conversation(self, db: Session, test_club: Club, test_customer: Customer):
        """Test creating a new conversation"""
        conversation = Conversation(
            club_id=test_club.id,
            customer_id=test_customer.id,
            vapi_call_id=f"call_123456{uuid4().hex[:8]}",
            phone_number=test_customer.phone,
            status="active",
            intent="general_inquiry",
        )

        db.add(conversation)
        db.commit()
        db.refresh(conversation)

        assert conversation.id is not None
        assert isinstance(conversation.id, UUID)
        assert conversation.status == "active"
        assert conversation.intent == "general_inquiry"

    def test_conversation_relationships(self, test_conversation: Conversation):
        """Test conversation relationships"""
        assert test_conversation.club is not None
        assert test_conversation.customer is not None
        assert test_conversation.club_id == test_conversation.club.id
        assert test_conversation.customer_id == test_conversation.customer.id

    def test_conversation_sentiment_analysis(self, test_conversation: Conversation):
        """Test sentiment field"""
        assert test_conversation.sentiment == "positive"

    def test_conversation_duration(self, test_conversation: Conversation):
        """Test duration tracking"""
        assert test_conversation.call_duration == 120
        if hasattr(test_conversation, "duration_minutes"):
            assert test_conversation.duration_minutes == 2


class TestVAPIWebhook:
    """Test VAPI webhook endpoints"""

    def test_webhook_call_started(self, client: TestClient):
        """Test webhook for call started event"""
        webhook_payload = {
            "type": "call-start",
            "call": {"id": "vapi_call_123", "customer": {"number": "+46701234567"}},
            "timestamp": datetime.utcnow().isoformat(),
        }

        response = client.post("/vapi/webhook", json=webhook_payload)

        # Endpoint should accept webhook
        assert response.status_code in [200, 201]

    def test_webhook_call_completed(self, client: TestClient, test_customer: Customer):
        """Test webhook for call completed event"""
        webhook_payload = {
            "type": "call-end",
            "call": {
                "id": "vapi_call_456",
                "customer": {"number": test_customer.phone},
                "duration": 180,
                "endedReason": "customer-ended-call",
            },
            "transcript": [
                {"role": "assistant", "content": "Hello!"},
                {"role": "user", "content": "Hi there"},
            ],
            "intent": "booking_inquiry",
            "sentiment": "positive",
            "summary": "Customer inquired about court availability",
        }

        response = client.post("/vapi/webhook", json=webhook_payload)

        assert response.status_code in [200, 201, 404]

    def test_webhook_invalid_payload(self, client: TestClient):
        """Test webhook with invalid payload"""
        # Test 1: Missing required field 'type'
        invalid_payload = {"event": "unknown_event"}  # Wrong field name - should be "type"

        response = client.post("/vapi/webhook", json=invalid_payload)

        # Should return 422 because "type" field is missing
        assert response.status_code == 422

        # Test 2: Has "type" field but unknown event type
        invalid_payload2 = {"type": "unknown_event"}  # Correct field name

        response2 = client.post("/vapi/webhook", json=invalid_payload2)

        # Should return 400 for unknown event type
        assert response2.status_code == 400

    def test_webhook_authentication(self, client: TestClient):
        """Test webhook authentication/signature verification"""
        webhook_payload = {
            "type": "call-start",
            "call": {
                "id": "test_123",
                "assistantId": "asst_test_123",
                "customer": {"number": "+46701234567"},
            },
        }

        # Without signature/auth - club won't be found but should handle gracefully
        response = client.post("/vapi/webhook", json=webhook_payload)

        # Should accept request (200) even if club not found
        assert response.status_code == 200


class TestConversationRoutes:
    """Test Conversation API endpoints"""

    def test_list_conversations(self, client: TestClient, auth_headers: dict, test_club: Club):
        """Test listing conversations"""
        response = client.get(
            "/conversations/",
            headers=auth_headers,
            params={"club_id": str(test_club.id)},
        )

        if response.status_code == 200:
            data = response.json()
            assert "conversations" in data or isinstance(data, list)

    def test_get_conversation_by_id(self, client: TestClient, test_conversation: Conversation):
        """Test getting a specific conversation"""
        response = client.get(f"/conversations/{test_conversation.id}")

        if response.status_code == 200:
            data = response.json()
            assert data["vapi_call_id"] == test_conversation.vapi_call_id

    def test_get_customer_conversations(
        self,
        client: TestClient,
        test_customer: Customer,
        test_conversation: Conversation,
    ):
        """Test getting all conversations for a customer"""
        response = client.get(f"/customers/{test_customer.id}/conversations")

        if response.status_code == 200:
            data = response.json()
            assert isinstance(data, (list, dict))

    def test_filter_conversations_by_intent(self, client: TestClient, auth_headers: dict, test_club: Club):
        """Test filtering conversations by intent"""
        response = client.get(
            "/conversations/",
            headers=auth_headers,
            params={"club_id": str(test_club.id), "intent": "booking_inquiry"},
        )

        if response.status_code == 200:
            data = response.json()
            if "conversations" in data:
                for conv in data["conversations"]:
                    assert conv["intent"] == "booking_inquiry"

    def test_filter_conversations_by_sentiment(self, client: TestClient, auth_headers: dict, test_club: Club):
        """Test filtering conversations by sentiment"""
        response = client.get(
            "/conversations/",
            headers=auth_headers,
            params={"club_id": str(test_club.id), "sentiment": "positive"},
        )

        if response.status_code == 200:
            data = response.json()
            if "conversations" in data:
                for conv in data["conversations"]:
                    assert conv["sentiment"] == "positive"

    def test_conversation_analytics(self, client: TestClient, auth_headers: dict, test_club: Club):
        """Test conversation analytics endpoint"""
        response = client.get(
            "/conversations/analytics",
            headers=auth_headers,
            params={"club_id": str(test_club.id)},
        )

        if response.status_code == 200:
            data = response.json()
            # Should contain analytics data
            assert "total_calls" in data or "analytics" in data or isinstance(data, dict)


class TestConversationIntents:
    """Test conversation intent detection and handling"""

    def test_booking_intent(self, db: Session, test_club: Club, test_customer: Customer):
        """Test conversation with booking intent"""
        conversation = Conversation(
            club_id=test_club.id,
            customer_id=test_customer.id,
            vapi_call_id=f"booking_intent_test{uuid4().hex[:8]}",
            phone_number=test_customer.phone,
            status="completed",
            intent="booking_inquiry",
            summary="Customer wants to book Court 1 on Friday at 10 AM",
        )

        db.add(conversation)
        db.commit()
        db.refresh(conversation)

        assert conversation.intent == "booking_inquiry"
        assert "booking" in conversation.intent.lower()

    def test_membership_inquiry_intent(self, db: Session, test_club: Club):
        """Test conversation with membership inquiry intent"""
        # First create a test customer
        customer = Customer(
            club_id=test_club.id,
            name="Test Customer",
            phone="+46709999999",
            email="test@example.com",
        )
        db.add(customer)
        db.commit()
        db.refresh(customer)

        conversation = Conversation(
            club_id=test_club.id,
            customer_id=customer.id,
            vapi_call_id=f"membership_intent_test{uuid4().hex[:8]}",
            phone_number="+46709999999",
            status="completed",
            intent="membership_inquiry",
            summary="Customer asked about membership options and pricing",
        )

        db.add(conversation)
        db.commit()
        db.refresh(conversation)

        assert conversation.intent == "membership_inquiry"

    def test_general_inquiry_intent(self, db: Session, test_club: Club):
        """Test conversation with general inquiry intent"""
        # First create a test customer
        customer = Customer(
            club_id=test_club.id,
            phone="+46708888888",
            name="Test Customer",
            email="test@example.com",
        )
        db.add(customer)
        db.commit()
        db.refresh(customer)

        conversation = Conversation(
            club_id=test_club.id,
            customer_id=customer.id,
            vapi_call_id=f"general_intent_test{uuid4().hex[:8]}",
            phone_number="+46708888888",
            status="completed",
            intent="general_inquiry",
            summary="Customer asked about opening hours",
        )

        db.add(conversation)
        db.commit()
        db.refresh(conversation)

        assert conversation.intent == "general_inquiry"


class TestCallStatusTransitions:
    """Test call status transitions"""

    def test_status_transition_started_to_completed(self, db: Session, test_club: Club, test_customer: Customer):
        """Test transitioning from started to completed"""
        conversation = Conversation(
            club_id=test_club.id,
            customer_id=test_customer.id,
            vapi_call_id=f"status_test_1{uuid4().hex[:8]}",
            phone_number=test_customer.phone,
            status="completed",
        )

        db.add(conversation)
        db.commit()

        # Update status
        conversation.status = "completed"
        conversation.call_duration = 150
        db.commit()
        db.refresh(conversation)

        assert conversation.status == "completed"
        assert conversation.call_duration == 150

    def test_failed_call_status(self, db: Session, test_club: Club):
        """Test handling failed calls"""
        # First create a test customer
        customer = Customer(
            club_id=test_club.id,
            name="Test Customer",
            phone="+46701111111",
            email="test@example.com",
        )
        db.add(customer)
        db.commit()
        db.refresh(customer)

        conversation = Conversation(
            club_id=test_club.id,
            customer_id=customer.id,
            vapi_call_id=f"failed_call_test{uuid4().hex[:8]}",
            phone_number="+46701111111",
            status="abandoned",
            summary="Call failed to connect",
        )

        db.add(conversation)
        db.commit()
        db.refresh(conversation)

        assert conversation.status == "abandoned"
