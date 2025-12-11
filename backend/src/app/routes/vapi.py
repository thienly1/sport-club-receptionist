"""
VAPI Webhook Routes
Handles webhooks from VAPI AI assistant
"""

import hashlib
import hmac
import logging
from datetime import datetime
from typing import Any, Dict, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, Header, HTTPException, Request, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.config import settings
from app.database import get_db
from app.models.booking import Booking, BookingStatus, BookingType
from app.models.club import Club
from app.models.conversation import (
    Conversation,
    ConversationStatus,
    Message,
    MessageRole,
)
from app.models.customer import Customer, CustomerStatus
from app.services.knowledge_base import KnowledgeBaseService
from app.services.matchi_service import MatchiService
from app.services.notification_service import NotificationService

logger = logging.getLogger(__name__)


# Define webhook validation models
class CallInfo(BaseModel):
    id: str
    assistantId: Optional[str] = None
    customer: Optional[Dict[str, Any]] = None
    duration: Optional[int] = None
    cost: Optional[float] = None
    endedReason: Optional[str] = None


class MessageInfo(BaseModel):
    role: str
    content: str
    id: Optional[str] = None


class FunctionCallInfo(BaseModel):
    name: str
    parameters: Dict[str, Any]


class VAPIWebhookPayload(BaseModel):
    type: str
    call: Optional[CallInfo] = None
    message: Optional[MessageInfo] = None
    functionCall: Optional[FunctionCallInfo] = None

    class Config:
        extra = "allow"  # Allow extra fields for future compatibility


router = APIRouter(prefix="/vapi", tags=["VAPI Webhooks"])


@router.get("/tools")
async def get_available_tools():
    """
    Return available tools for VAPI assistant
    This supports VAPI's new Tools system
    """
    return {
        "tools": [
            {
                "type": "function",
                "function": {
                    "name": "create_booking",
                    "description": "Creates a booking after collecting all customer information",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "customer_name": {
                                "type": "string",
                                "description": "Customer's full name",
                            },
                            "customer_phone": {
                                "type": "string",
                                "description": "Phone number with country code (e.g., +46701234567)",
                            },
                            "activity": {
                                "type": "string",
                                "description": "Type of activity to book",
                                "enum": ["tennis", "padel", "gym"],
                            },
                            "booking_date": {
                                "type": "string",
                                "description": "Date in YYYY-MM-DD format",
                            },
                            "booking_time": {
                                "type": "string",
                                "description": "Start time in HH:MM format (24-hour)",
                            },
                        },
                        "required": [
                            "customer_name",
                            "customer_phone",
                            "activity",
                            "booking_date",
                            "booking_time",
                        ],
                    },
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "escalate_to_manager",
                    "description": "Escalate complex questions to club manager",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "customer_name": {
                                "type": "string",
                                "description": "Customer's name",
                            },
                            "customer_phone": {
                                "type": "string",
                                "description": "Customer's phone number",
                            },
                            "question": {
                                "type": "string",
                                "description": "The question that needs manager attention",
                            },
                        },
                        "required": ["customer_name", "customer_phone", "question"],
                    },
                },
            },
        ]
    }


def verify_vapi_signature(payload: bytes, signature: str) -> bool:
    """Verify VAPI webhook signature"""
    if not signature:
        return False

    expected_signature = hmac.new(settings.VAPI_WEBHOOK_SECRET.encode(), payload, hashlib.sha256).hexdigest()

    return hmac.compare_digest(signature, expected_signature)


@router.post("/webhook")
async def vapi_webhook(
    request: Request,
    x_vapi_signature: Optional[str] = Header(None),
    db: Session = Depends(get_db),
):
    """
    Main VAPI webhook endpoint
    Handles all events from VAPI assistant
    """
    # Get raw body for signature verification
    body = await request.body()

    # Verify signature in production
    if settings.ENVIRONMENT == "production":
        if not verify_vapi_signature(body, x_vapi_signature):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid webhook signature",
            )

    # Try to parse JSON
    try:
        data = await request.json()
    except Exception as e:
        print(f"Non-JSON request received: {e}")
        # If not JSON (like 46elks form data), return success
        return {"status": "ok", "message": "Non-JSON request received"}

    # Validate with Pydantic (after successful JSON parsing)
    try:
        validated_data = VAPIWebhookPayload(**data)
    except Exception as validation_error:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Invalid payload: {str(validation_error)}",
        )

    # Use validated data
    event_type = validated_data.type  # Use validated_data, not data

    # Convert validated data back to dict for handlers (they expect dict)
    data_dict = validated_data.dict()

    # Route to appropriate handler
    if event_type == "call-start":
        return await handle_call_start(data_dict, db)
    elif event_type == "call-end":
        return await handle_call_end(data_dict, db)
    elif event_type == "function-call":
        return await handle_function_call(data_dict, db)
    elif event_type == "message":
        return await handle_message(data_dict, db)
    elif event_type == "transcript":
        return await handle_transcript(data_dict, db)
    else:
        # Return 400 for unknown event types
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unknown event type: {event_type}",
        )


async def handle_call_start(data: Dict[str, Any], db: Session) -> Dict[str, Any]:
    """Handle call start event"""
    call_id = data.get("call", {}).get("id")
    phone_number = data.get("call", {}).get("customer", {}).get("number")
    assistant_id = data.get("call", {}).get("assistantId")

    # Validate required fields
    if not call_id:
        return {"status": "error", "message": "Missing call ID"}

    if not phone_number:
        return {"status": "error", "message": "Missing phone number"}

    # Find club by assistant ID
    club = None
    if assistant_id:
        club = db.query(Club).filter(Club.ai_assistant_id == assistant_id).first()

    if not club:
        return {"status": "error", "message": "Club not found"}

    # Find or create customer
    customer = db.query(Customer).filter(Customer.phone == phone_number, Customer.club_id == club.id).first()

    if not customer:
        # Create new customer/lead
        customer = Customer(
            club_id=club.id,
            name="Unknown Caller",  # Will be updated during call
            phone=phone_number,
            source="phone_call",
            status=CustomerStatus.LEAD,
        )
        db.add(customer)
        db.commit()
        db.refresh(customer)

    # Create conversation record
    conversation = Conversation(
        club_id=club.id,
        customer_id=customer.id,
        vapi_call_id=call_id,
        vapi_assistant_id=assistant_id,
        phone_number=phone_number,
        status=ConversationStatus.ACTIVE,
        started_at=datetime.utcnow(),
    )
    db.add(conversation)
    db.commit()

    return {
        "status": "ok",
        "conversation_id": str(conversation.id),
        "customer_id": str(customer.id),
    }


async def handle_call_end(data: Dict[str, Any], db: Session) -> Dict[str, Any]:
    """Handle call end event"""
    call_id = data.get("call", {}).get("id")
    duration = data.get("call", {}).get("duration")
    cost = data.get("call", {}).get("cost")
    ended_reason = data.get("call", {}).get("endedReason")

    # Find conversation
    conversation = db.query(Conversation).filter(Conversation.vapi_call_id == call_id).first()

    if conversation:
        conversation.status = ConversationStatus.COMPLETED
        conversation.ended_at = datetime.utcnow()
        conversation.call_duration = duration
        conversation.call_cost = cost
        conversation.outcome = ended_reason

        db.commit()

    return {"status": "ok"}


async def handle_function_call(data: Dict[str, Any], db: Session) -> Dict[str, Any]:
    """
    Handle function calls from VAPI assistant
    This is where the AI assistant calls our backend functions
    """
    function_name = data.get("functionCall", {}).get("name")
    parameters = data.get("functionCall", {}).get("parameters", {})
    call_id = data.get("call", {}).get("id")

    # Find conversation
    conversation = db.query(Conversation).filter(Conversation.vapi_call_id == call_id).first()

    if not conversation:
        return {"error": "Conversation not found"}

    # Route to appropriate function handler
    if function_name == "get_membership_info":
        return get_membership_info(conversation.club_id, db)

    elif function_name == "get_availability":
        return get_availability(parameters, db)

    elif function_name == "create_booking":
        return await create_booking_from_call(parameters, conversation, db)

    elif function_name == "save_customer_info":
        return save_customer_info(parameters, conversation, db)

    elif function_name == "escalate_to_manager":
        return await escalate_to_manager(parameters, conversation, db)

    elif function_name == "get_matchi_booking_link":
        return get_matchi_booking_link(conversation.club_id, db)

    else:
        return {"error": f"Unknown function: {function_name}"}


async def handle_message(data: Dict[str, Any], db: Session) -> Dict[str, Any]:
    """Handle message events"""
    call_id = data.get("call", {}).get("id")
    message_data = data.get("message", {})

    conversation = db.query(Conversation).filter(Conversation.vapi_call_id == call_id).first()

    if conversation:
        # Map VAPI role to database enum value
        vapi_role = message_data.get("role", "user").lower()
        if vapi_role == "assistant":
            db_role = MessageRole.ASSISTANT.value  # Gets "assistant"
        else:
            db_role = MessageRole.CUSTOMER.value  # Gets "customer"

        # Store message
        message = Message(
            conversation_id=conversation.id,
            role=db_role,  # Now using lowercase string
            content=message_data.get("content", ""),
            vapi_message_id=message_data.get("id"),
            timestamp=datetime.utcnow(),
        )
        db.add(message)
        db.commit()

    return {"status": "ok"}


async def handle_transcript(data: Dict[str, Any], db: Session) -> Dict[str, Any]:
    """Handle transcript events"""
    # Update conversation with transcript data
    return {"status": "ok"}


# Function handlers


def get_membership_info(club_id: UUID, db: Session) -> Dict[str, Any]:
    """Get membership information"""
    memberships = KnowledgeBaseService.get_membership_info(db, club_id)

    if not memberships:
        return {"message": "No membership information available"}

    # Format for AI response
    response = "We offer the following memberships:\n"
    for m in memberships:
        response += f"- {m['name']}: {m['price']} {m['currency']} per {m['period']}\n"

    return {"result": response}


def get_availability(parameters: Dict[str, Any], db: Session) -> Dict[str, Any]:
    """Check availability"""
    date = parameters.get("date")
    time = parameters.get("time")

    # Use Matchi service
    matchi_service = MatchiService()
    availability = matchi_service.check_availability(date, time, "Court")

    # Use the result
    if availability and availability.get("available"):
        return {"result": f"There is availability on {date} at {time}. " f"Would you like me to book it for you?"}
    return {
        "result": f"Please check our booking system for availability on {date} at {time}. "
        f"You can book online at our Matchi page."
    }


async def create_booking_from_call(
    parameters: Dict[str, Any], conversation: Conversation, db: Session
) -> Dict[str, Any]:
    """Create booking from phone call"""
    try:
        # Parse datetime
        booking_date = datetime.fromisoformat(parameters["booking_date"])

        # Handle booking_time (single time) - default 1 hour duration
        if "booking_time" in parameters:
            start_time = datetime.fromisoformat(f"{parameters['booking_date']}T{parameters['booking_time']}")
            # Default to 1 hour booking
            end_time = datetime.fromisoformat(f"{parameters['booking_date']}T{parameters['booking_time']}")
            from datetime import timedelta

            end_time = start_time + timedelta(hours=1)
        else:
            # Fallback to start_time/end_time if provided
            start_time = datetime.fromisoformat(f"{parameters['booking_date']}T{parameters.get('start_time', '10:00')}")
            end_time = datetime.fromisoformat(f"{parameters['booking_date']}T{parameters.get('end_time', '11:00')}")

        # Map activity to resource name
        activity = parameters.get("activity", "court")
        resource_map = {
            "tennis": "Tennis Court",
            "padel": "Padel Court",
            "gym": "Gym Session",
        }
        resource_name = resource_map.get(activity.lower(), activity.title())

        # Create booking
        booking = Booking(
            club_id=conversation.club_id,
            customer_id=conversation.customer_id,
            conversation_id=conversation.id,
            booking_type=BookingType.COURT,
            status=BookingStatus.PENDING,
            resource_name=resource_name,
            booking_date=booking_date,
            start_time=start_time,
            end_time=end_time,
            contact_name=parameters["customer_name"],
            contact_phone=parameters["customer_phone"],
            contact_email=parameters.get("customer_email"),
            notes=parameters.get("notes"),
            confirmation_code=f"BK{datetime.now().strftime('%Y%m%d%H%M')}",
        )
        db.add(booking)
        db.commit()
        db.refresh(booking)

        # Send SMS confirmation
        try:
            notification_service = NotificationService()
            notification_service.send_booking_confirmation(db, booking.id)
        except Exception as sms_error:
            logger.error(f"Failed to send SMS confirmation: {sms_error}")

        return {
            "result": f"Booking created! Confirmation code: {booking.confirmation_code}. "
            f"You'll receive an SMS confirmation shortly."
        }

    except Exception as e:
        return {"error": f"Failed to create booking: {str(e)}"}


def save_customer_info(parameters: Dict[str, Any], conversation: Conversation, db: Session) -> Dict[str, Any]:
    """Save or update customer information"""
    customer = db.query(Customer).filter(Customer.id == conversation.customer_id).first()

    if customer:
        # Update customer
        if "name" in parameters and parameters["name"] != "Unknown Caller":
            customer.name = parameters["name"]
        if "email" in parameters:
            customer.email = parameters["email"]
        if "interested_in" in parameters:
            customer.interested_in = parameters["interested_in"]
        if "notes" in parameters:
            customer.notes = parameters["notes"]

        customer.status = CustomerStatus.INTERESTED
        customer.last_contact_date = datetime.utcnow()

        db.commit()

    return {"result": "Customer information saved successfully"}


async def escalate_to_manager(parameters: Dict[str, Any], conversation: Conversation, db: Session) -> Dict[str, Any]:
    """Escalate question to manager"""
    notification_service = NotificationService()

    result = notification_service.send_escalation_to_manager(
        db=db,
        club_id=conversation.club_id,
        customer_name=parameters["customer_name"],
        customer_phone=parameters["customer_phone"],
        question=parameters["question"],
        conversation_id=conversation.id,
    )

    # Update conversation
    conversation.escalated_to_manager = True
    conversation.status = ConversationStatus.ESCALATED
    db.commit()

    if result.get("success"):
        return {
            "result": "I've forwarded your question to our manager. "
            "They'll contact you shortly to help with your inquiry."
        }
    else:
        return {
            "result": "I'll make sure someone gets back to you about this. "
            "Is there anything else I can help you with right now?"
        }


def get_matchi_booking_link(club_id: UUID, db: Session) -> Dict[str, Any]:
    """Get Matchi booking link"""
    matchi_service = MatchiService()
    url = matchi_service.get_booking_url(db, club_id)
    instructions = matchi_service.generate_booking_instructions(db, club_id)

    return {"result": instructions, "booking_url": url}
