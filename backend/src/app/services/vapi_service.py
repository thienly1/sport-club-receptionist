"""
VAPI Integration Service
Handles integration with VAPI AI assistant platform
"""

from typing import Any, Dict, List, Optional
from uuid import UUID

import httpx
from sqlalchemy.orm import Session

from app.config import settings
from app.models.club import Club
from app.services.knowledge_base import KnowledgeBaseService


class VAPIService:
    """Service for integrating with VAPI AI voice assistant"""

    def __init__(self):
        self.api_key = settings.VAPI_API_KEY
        self.base_url = settings.VAPI_BASE_URL
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

    async def create_assistant(
        self, db: Session, club_id: UUID, name: str, voice: str = "jennifer-playht"
    ) -> Dict[str, Any]:
        """
        Create a VAPI assistant for a club

        Args:
            db: Database session
            club_id: Club UUID
            name: Assistant name
            voice: Voice to use

        Returns:
            Assistant creation result
        """
        # Get club knowledge base
        knowledge = KnowledgeBaseService.format_for_ai_prompt(db, club_id)

        # Define functions the assistant can call
        functions = self._get_assistant_functions()

        # Create assistant configuration
        assistant_config = {
            "name": name,
            "voice": {"provider": "playht", "voiceId": voice},
            "model": {
                "provider": "openai",
                "model": "gpt-4",
                "temperature": 0.7,
                "systemPrompt": self._build_system_prompt(knowledge),
                "functions": functions,
            },
            "firstMessage": self._get_greeting(db, club_id),
            "endCallFunctionEnabled": True,
            "recordingEnabled": True,
            "hipaaEnabled": False,
            "silenceTimeoutSeconds": 30,
            "maxDurationSeconds": 600,  # 10 minutes max
            "backgroundSound": "office",
        }

        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.base_url}/assistant",
                    headers=self.headers,
                    json=assistant_config,
                    timeout=30.0,
                )
                response.raise_for_status()
                result = response.json()

                # Update club with assistant ID
                club = db.query(Club).filter(Club.id == club_id).first()
                if club:
                    club.ai_assistant_id = result.get("id")
                    db.commit()

                return {
                    "success": True,
                    "assistant_id": result.get("id"),
                    "data": result,
                }

        except Exception as e:
            return {"success": False, "error": str(e)}

    async def update_assistant(self, db: Session, club_id: UUID, assistant_id: str) -> Dict[str, Any]:
        """
        Update VAPI assistant with latest club information

        Args:
            db: Database session
            club_id: Club UUID
            assistant_id: VAPI assistant ID

        Returns:
            Update result
        """
        knowledge = KnowledgeBaseService.format_for_ai_prompt(db, club_id)

        update_config = {
            "model": {"systemPrompt": self._build_system_prompt(knowledge)},
            "firstMessage": self._get_greeting(db, club_id),
        }

        try:
            async with httpx.AsyncClient() as client:
                response = await client.patch(
                    f"{self.base_url}/assistant/{assistant_id}",
                    headers=self.headers,
                    json=update_config,
                    timeout=30.0,
                )
                response.raise_for_status()

                return {"success": True, "data": response.json()}

        except Exception as e:
            return {"success": False, "error": str(e)}

    def _build_system_prompt(self, knowledge_base: str) -> str:
        """Build system prompt for the AI assistant"""

        return f"""
        You are an AI receptionist for a sport club. Your role is to:

        1. Answer questions about membership, pricing, facilities, and policies
        2. Provide directions and practical information
        3. Guide customers to book through Matchi
        4. Collect customer information for new leads
        5. Handle phone bookings when necessary
        6. Escalate complex questions to the manager

        IMPORTANT GUIDELINES:
        - Be friendly, professional, and helpful
        - Keep responses concise and clear
        - Speak naturally, as if in a phone conversation
        - If you don't know something, be honest and offer to connect them with the manager
        - Always collect customer name and phone number for follow-up
        - For bookings, first try to direct them to Matchi, but offer phone booking if they prefer
        - Don't make up information - only use the club knowledge provided

        CLUB INFORMATION:
        {knowledge_base}

        Remember: You're here to help potential customers learn about the club and become members!
        """.strip()

    def _get_greeting(self, db: Session, club_id: UUID) -> str:
        """Get greeting message for the assistant"""
        club = db.query(Club).filter(Club.id == club_id).first()

        if club and club.custom_greeting:
            return club.custom_greeting

        default_greeting = f"Hello! Thank you for calling {club.name if club else 'us'}. My name is Alex, your AI assistant. How can I help you today?"
        return default_greeting

    def _get_assistant_functions(self) -> List[Dict[str, Any]]:
        """
        Define functions the AI assistant can call
        These map to your API endpoints
        """
        return [
            {
                "name": "get_membership_info",
                "description": "Get detailed membership types and pricing",
                "parameters": {"type": "object", "properties": {}, "required": []},
            },
            {
                "name": "get_availability",
                "description": "Check availability for a specific date and time",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "date": {
                            "type": "string",
                            "description": "Date in YYYY-MM-DD format",
                        },
                        "time": {
                            "type": "string",
                            "description": "Time in HH:MM format",
                        },
                    },
                    "required": ["date", "time"],
                },
            },
            {
                "name": "create_booking",
                "description": "Create a phone booking for the customer",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "customer_name": {"type": "string"},
                        "customer_phone": {"type": "string"},
                        "customer_email": {"type": "string"},
                        "booking_date": {"type": "string"},
                        "start_time": {"type": "string"},
                        "end_time": {"type": "string"},
                        "resource": {"type": "string"},
                        "notes": {"type": "string"},
                    },
                    "required": [
                        "customer_name",
                        "customer_phone",
                        "booking_date",
                        "start_time",
                        "end_time",
                    ],
                },
            },
            {
                "name": "save_customer_info",
                "description": "Save customer information as a new lead",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "name": {"type": "string"},
                        "phone": {"type": "string"},
                        "email": {"type": "string"},
                        "interested_in": {"type": "string"},
                        "notes": {"type": "string"},
                    },
                    "required": ["name", "phone"],
                },
            },
            {
                "name": "escalate_to_manager",
                "description": "Escalate question to club manager via SMS",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "customer_name": {"type": "string"},
                        "customer_phone": {"type": "string"},
                        "question": {"type": "string"},
                        "reason": {"type": "string"},
                    },
                    "required": ["customer_name", "customer_phone", "question"],
                },
            },
            {
                "name": "get_matchi_booking_link",
                "description": "Get the Matchi booking link for online booking",
                "parameters": {"type": "object", "properties": {}, "required": []},
            },
        ]

    async def make_outbound_call(
        self, phone_number: str, assistant_id: str, customer_name: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Make an outbound call using VAPI

        Args:
            phone_number: Number to call
            assistant_id: VAPI assistant ID to use
            customer_name: Optional customer name for personalization

        Returns:
            Call result
        """
        call_config = {
            "assistantId": assistant_id,
            "phoneNumber": phone_number,
            "customerName": customer_name,
        }

        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.base_url}/call",
                    headers=self.headers,
                    json=call_config,
                    timeout=30.0,
                )
                response.raise_for_status()

                return {"success": True, "data": response.json()}

        except Exception as e:
            return {"success": False, "error": str(e)}
