"""
Conversation API Routes
Endpoints for viewing conversation history and analytics
"""

from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.conversation import Conversation, Message
from app.schemas.conversation import ConversationDetail, ConversationList

router = APIRouter(prefix="/conversations", tags=["Conversations"])


@router.get("/", response_model=ConversationList)
def list_conversations(
    club_id: Optional[UUID] = None,
    customer_id: Optional[UUID] = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db),
):
    """List conversations with filters"""
    query = db.query(Conversation)

    if club_id:
        query = query.filter(Conversation.club_id == club_id)

    if customer_id:
        query = query.filter(Conversation.customer_id == customer_id)

    total = query.count()
    conversations = query.order_by(Conversation.started_at.desc()).offset(skip).limit(limit).all()

    return {
        "conversations": conversations,
        "total": total,
        "page": (skip // limit) + 1,
        "page_size": limit,
    }


@router.get("/{conversation_id}", response_model=ConversationDetail)
def get_conversation(conversation_id: UUID, db: Session = Depends(get_db)):
    """Get a specific conversation with all messages"""
    conversation = db.query(Conversation).filter(Conversation.id == conversation_id).first()

    if not conversation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Conversation with ID {conversation_id} not found",
        )

    return conversation


@router.get("/{conversation_id}/messages")
def get_conversation_messages(conversation_id: UUID, db: Session = Depends(get_db)):
    """Get all messages in a conversation"""
    conversation = db.query(Conversation).filter(Conversation.id == conversation_id).first()

    if not conversation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Conversation with ID {conversation_id} not found",
        )

    messages = db.query(Message).filter(Message.conversation_id == conversation_id).order_by(Message.timestamp).all()

    return {
        "conversation_id": conversation_id,
        "messages": messages,
        "total": len(messages),
    }
