"""
Club API Routes
Endpoints for managing sport clubs
"""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies.auth import get_current_active_user, get_super_admin
from app.models.club import Club
from app.models.user import User
from app.schemas.club import ClubCreate, ClubList, ClubResponse, ClubUpdate
from app.services.vapi_service import VAPIService

router = APIRouter(prefix="/clubs", tags=["Clubs"])


@router.post("/", response_model=ClubResponse, status_code=status.HTTP_201_CREATED)
async def create_club(
    club_data: ClubCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_super_admin),
):
    """
    Create a new sport club

    This will also create a VAPI assistant for the club
    """
    # Check if slug already exists
    if current_user:
        existing = db.query(Club).filter(Club.slug == club_data.slug).first()
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Club with slug '{club_data.slug}' already exists",
            )

        # Check if email already exists
        existing_email = db.query(Club).filter(Club.email == club_data.email).first()
        if existing_email:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Club with email '{club_data.email}' already exists",
            )

        # Create club
        club = Club(**club_data.model_dump())
        db.add(club)
        db.commit()
        db.refresh(club)

        # Create VAPI assistant
        vapi_service = VAPIService()
        assistant_result = await vapi_service.create_assistant(db=db, club_id=club.id, name=f"{club.name} Receptionist")

        if assistant_result.get("success"):
            club.ai_assistant_id = assistant_result.get("assistant_id")
            db.commit()
            db.refresh(club)

        return club


@router.get("/", response_model=ClubList)
def list_clubs(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    active_only: bool = Query(True),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    List clubs with pagination

    - Super admins see all clubs
    - Club admins and staff see only their assigned club
    """
    query = db.query(Club)

    # Filter by user role
    if current_user.role in ["club_admin", "club_staff"]:
        if current_user.club_id is None:
            # User has no club assigned
            return {"clubs": [], "total": 0, "page": 1, "page_size": limit}
        query = query.filter(Club.id == current_user.club_id)

    if active_only:
        query = query.filter(Club.is_active.is_(True))

    total = query.count()
    clubs = query.offset(skip).limit(limit).all()

    return {
        "clubs": clubs,
        "total": total,
        "page": (skip // limit) + 1,
        "page_size": limit,
    }


@router.get("/{club_id}", response_model=ClubResponse)
def get_club(club_id: UUID, db: Session = Depends(get_db)):
    """Get a specific club by ID"""
    club = db.query(Club).filter(Club.id == club_id).first()

    if not club:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Club with ID {club_id} not found",
        )

    return club


@router.get("/slug/{slug}", response_model=ClubResponse)
def get_club_by_slug(slug: str, db: Session = Depends(get_db)):
    """Get a specific club by slug"""
    club = db.query(Club).filter(Club.slug == slug).first()

    if not club:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Club with slug '{slug}' not found",
        )

    return club


@router.patch("/{club_id}", response_model=ClubResponse)
async def update_club(
    club_id: UUID,
    club_data: ClubUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):

    # Add authorization check
    if current_user.role not in ["super_admin", "club_admin"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions to update club",
        )

    # If user is club_admin, verify they belong to this club
    if current_user.role == "club_admin" and current_user.club_id != club_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Can only update your own club",
        )
    if current_user.role in ["club_admin", "super_admin"]:
        """Update a club's information"""
        club = db.query(Club).filter(Club.id == club_id).first()

        if not club:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Club with ID {club_id} not found",
            )

        # Update fields
        update_data = club_data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(club, field, value)

        db.commit()
        db.refresh(club)

        # Update VAPI assistant if knowledge base changed
        if club.ai_assistant_id and any(
            k in update_data
            for k in [
                "membership_types",
                "pricing_info",
                "opening_hours",
                "policies",
                "knowledge_base",
            ]
        ):
            vapi_service = VAPIService()
            await vapi_service.update_assistant(db, club_id, club.ai_assistant_id)

        return club


@router.delete("/{club_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_club(
    club_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_super_admin),
):
    if current_user:
        """Delete a club (soft delete by setting is_active=False)"""
        club = db.query(Club).filter(Club.id == club_id).first()

        if not club:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Club with ID {club_id} not found",
            )

        # Soft delete
        club.is_active = False
        db.commit()

        return None


@router.post("/{club_id}/sync-assistant")
async def sync_vapi_assistant(club_id: UUID, db: Session = Depends(get_db)):
    """Manually sync club information to VAPI assistant"""
    club = db.query(Club).filter(Club.id == club_id).first()

    if not club:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Club with ID {club_id} not found",
        )

    vapi_service = VAPIService()

    if not club.ai_assistant_id:
        # Create new assistant
        result = await vapi_service.create_assistant(db=db, club_id=club_id, name=f"{club.name} Receptionist")
    else:
        # Update existing assistant
        result = await vapi_service.update_assistant(db=db, club_id=club_id, assistant_id=club.ai_assistant_id)

    if not result.get("success"):
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to sync assistant: {result.get('error')}",
        )

    return {
        "message": "Assistant synced successfully",
        "assistant_id": club.ai_assistant_id,
    }
