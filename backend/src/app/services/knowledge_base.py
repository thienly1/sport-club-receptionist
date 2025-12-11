"""
Knowledge Base Service
Retrieves club information for the AI assistant
"""

from typing import Any, Dict, List, Optional
from uuid import UUID

from sqlalchemy.orm import Session

from app.models.club import Club


class KnowledgeBaseService:
    """
    Service for managing club knowledge base and information retrieval
    This is what the AI assistant uses to answer questions
    """

    @staticmethod
    def get_club_info(db: Session, club_id: UUID) -> Optional[Dict[str, Any]]:
        """
        Get comprehensive club information for AI assistant

        Args:
            db: Database session
            club_id: Club UUID

        Returns:
            Dictionary with all club information
        """
        club = db.query(Club).filter(Club.id == club_id, Club.is_active.is_(True)).first()

        if not club:
            return None

        return {
            "club_name": club.name,
            "phone": club.phone,
            "email": club.email,
            "address": club.address,
            "city": club.city,
            "postal_code": club.postal_code,
            "description": club.description,
            "website": club.website,
            "membership_types": club.membership_types,
            "pricing_info": club.pricing_info,
            "facilities": club.facilities,
            "opening_hours": club.opening_hours,
            "policies": club.policies,
            "matchi_booking_url": club.matchi_booking_url,
            "custom_greeting": club.custom_greeting,
            "knowledge_base": club.knowledge_base,
        }

    @staticmethod
    def get_membership_info(db: Session, club_id: UUID) -> List[Dict[str, Any]]:
        """Get membership types and pricing"""
        club = db.query(Club).filter(Club.id == club_id).first()
        if not club:
            return []
        return club.membership_types or []

    @staticmethod
    def get_pricing_info(db: Session, club_id: UUID) -> Dict[str, Any]:
        """Get all pricing information"""
        club = db.query(Club).filter(Club.id == club_id).first()
        if not club:
            return {}
        return club.pricing_info or {}

    @staticmethod
    def get_facilities(db: Session, club_id: UUID) -> List[str]:
        """Get list of facilities"""
        club = db.query(Club).filter(Club.id == club_id).first()
        if not club:
            return []
        return club.facilities or []

    @staticmethod
    def get_opening_hours(db: Session, club_id: UUID) -> Dict[str, Dict[str, str]]:
        """Get opening hours for all days"""
        club = db.query(Club).filter(Club.id == club_id).first()
        if not club:
            return {}
        return club.opening_hours or {}

    @staticmethod
    def get_policies(db: Session, club_id: UUID) -> Optional[str]:
        """Get club policies and rules"""
        club = db.query(Club).filter(Club.id == club_id).first()
        if not club:
            return None
        return club.policies

    @staticmethod
    def get_directions(db: Session, club_id: UUID) -> Dict[str, str]:
        """Get location and directions"""
        club = db.query(Club).filter(Club.id == club_id).first()
        if not club:
            return {}

        return {
            "address": club.address,
            "city": club.city,
            "postal_code": club.postal_code,
            "directions": (f"{club.address}, {club.postal_code} {club.city}" if club.address else None),
        }

    @staticmethod
    def search_knowledge_base(db: Session, club_id: UUID, query: str) -> Optional[str]:
        """
        Search custom knowledge base for specific Q&A

        Args:
            db: Database session
            club_id: Club UUID
            query: Search query

        Returns:
            Answer if found, None otherwise
        """
        club = db.query(Club).filter(Club.id == club_id).first()
        if not club or not club.knowledge_base:
            return None

        # Simple keyword matching in knowledge base
        query_lower = query.lower()
        kb = club.knowledge_base

        # Check if knowledge base has FAQ structure
        if isinstance(kb, dict) and "faq" in kb:
            for qa in kb["faq"]:
                if query_lower in qa.get("question", "").lower():
                    return qa.get("answer")

        return None

    @staticmethod
    def format_for_ai_prompt(db: Session, club_id: UUID) -> str:
        """
        Format club information as a prompt for the AI assistant

        Args:
            db: Database session
            club_id: Club UUID

        Returns:
            Formatted string for AI prompt
        """
        info = KnowledgeBaseService.get_club_info(db, club_id)
        if not info:
            return ""

        prompt_parts = []

        # Basic info
        prompt_parts.append(f"You are the AI receptionist for {info['club_name']}.")

        if info.get("description"):
            prompt_parts.append(f"About us: {info['description']}")

        # Contact
        prompt_parts.append("\nContact Information: ")
        prompt_parts.append(f"- Phone: {info['phone']}")
        prompt_parts.append(f"- Email: {info['email']}")
        if info.get("address"):
            prompt_parts.append(f"- Address: {info['address']}, {info['postal_code']} {info['city']}")

        # Memberships
        if info.get("membership_types"):
            prompt_parts.append("\nMembership Types: ")
            for membership in info["membership_types"]:
                prompt_parts.append(
                    f"- {membership['name']}: {membership['price']} {membership['currency']}/{membership['period']}"
                )

        # Facilities
        if info.get("facilities"):
            prompt_parts.append(f"\nFacilities: {', '.join(info['facilities'])}")

        # Opening hours
        if info.get("opening_hours"):
            prompt_parts.append("\nOpening Hours: ")
            for day, hours in info["opening_hours"].items():
                if hours.get("closed"):
                    prompt_parts.append(f"- {day.capitalize()}: Closed")
                else:
                    prompt_parts.append(f"- {day.capitalize()}: {hours['open']} - {hours['close']}")

        # Booking info
        if info.get("matchi_booking_url"):
            prompt_parts.append(f"\nFor bookings, direct customers to: {info['matchi_booking_url']}")

        # Policies
        if info.get("policies"):
            prompt_parts.append(f"\nPolicies: {info['policies']}")

        return "\n".join(prompt_parts)
