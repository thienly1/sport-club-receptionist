"""
Customer API Routes
Endpoints for managing customers and leads
"""

from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies.auth import get_current_active_user
from app.models.customer import Customer
from app.models.user import User
from app.schemas.customer import (
    CustomerCreate,
    CustomerList,
    CustomerResponse,
    CustomerStatus,
    CustomerUpdate,
)
from app.services.notification_service import NotificationService

router = APIRouter(prefix="/customers", tags=["Customers"])


@router.post("/", response_model=CustomerResponse, status_code=status.HTTP_201_CREATED)
async def create_customer(
    customer_data: CustomerCreate,
    send_lead_alert: bool = Query(False, description="Send SMS alert to manager"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),  # FIXED: This ensures auth
):
    """Create a new customer/lead"""
    # Create customer
    customer = Customer(**customer_data.model_dump())

    # Set club_id if not provided and user is club staff/admin
    if not customer.club_id and current_user.club_id:
        customer.club_id = current_user.club_id

    # For super admin, require club_id to be explicitly provided
    if not customer.club_id and current_user.is_super_admin:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="club_id is required for super admin",
        )

    # Check permission: club staff/admin can only create customers in their club
    if not current_user.is_super_admin and customer.club_id != current_user.club_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Cannot create customer in another club",
        )

    db.add(customer)
    db.commit()
    db.refresh(customer)

    # Send lead alert if requested
    if send_lead_alert:
        notification_service = NotificationService()
        await notification_service.send_lead_alert(db=db, club_id=customer.club_id, customer_id=customer.id)

    return customer


@router.get("/", response_model=CustomerList)
def list_customers(
    status: Optional[CustomerStatus] = None,
    requires_follow_up: Optional[bool] = None,
    search: Optional[str] = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),  # FIXED: Requires auth
):
    """List customers with filters"""
    query = db.query(Customer)

    # Apply club filter for non-super-admin users
    if not current_user.is_super_admin:
        if not current_user.club_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="User is not associated with any club",
            )
        query = query.filter(Customer.club_id == current_user.club_id)

    # Apply filters
    if status:
        query = query.filter(Customer.status == status)

    if requires_follow_up is not None:
        query = query.filter(Customer.requires_follow_up == requires_follow_up)

    if search:
        search_term = f"%{search}%"
        query = query.filter(
            or_(
                Customer.name.ilike(search_term),
                Customer.phone.ilike(search_term),
                Customer.email.ilike(search_term),
            )
        )

    total = query.count()
    customers = query.order_by(Customer.created_at.desc()).offset(skip).limit(limit).all()

    return {
        "customers": customers,
        "total": total,
        "page": (skip // limit) + 1,
        "page_size": limit,
    }


@router.get("/{customer_id}", response_model=CustomerResponse)
def get_customer(
    customer_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),  # FIXED: Requires auth
):
    """Get a specific customer"""
    query = db.query(Customer).filter(Customer.id == customer_id)

    # Club staff/admin can only see customers in their club
    if not current_user.is_super_admin:
        if not current_user.club_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="User is not associated with any club",
            )
        query = query.filter(Customer.club_id == current_user.club_id)

    customer = query.first()

    if not customer:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Customer with ID {customer_id} not found",
        )

    return customer


@router.patch("/{customer_id}", response_model=CustomerResponse)
def update_customer(
    customer_id: UUID,
    customer_data: CustomerUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),  # FIXED: Requires auth
):
    """Update customer information"""
    query = db.query(Customer).filter(Customer.id == customer_id)

    # Club staff/admin can only update customers in their club
    if not current_user.is_super_admin:
        if not current_user.club_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="User is not associated with any club",
            )
        query = query.filter(Customer.club_id == current_user.club_id)

    customer = query.first()

    if not customer:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Customer with ID {customer_id} not found",
        )

    # Check if trying to update club_id (only super admin can do this)
    if "club_id" in customer_data.model_dump(exclude_unset=True) and not current_user.is_super_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only super admin can change customer's club",
        )

    # Update fields
    update_data = customer_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(customer, field, value)

    db.commit()
    db.refresh(customer)

    return customer


@router.get("/phone/{phone}", response_model=CustomerResponse)
def get_customer_by_phone(
    phone: str,
    club_id: Optional[UUID] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),  # FIXED: Added auth
):
    """Find customer by phone number"""
    query = db.query(Customer).filter(Customer.phone == phone)

    # If club_id is provided, use it; otherwise use user's club
    if club_id:
        query = query.filter(Customer.club_id == club_id)
    elif not current_user.is_super_admin:
        # Club staff/admin can only search in their club
        if not current_user.club_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="User is not associated with any club",
            )
        query = query.filter(Customer.club_id == current_user.club_id)
    # Super admin without club_id can search across all clubs

    customer = query.first()

    if not customer:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Customer with phone {phone} not found",
        )

    # Additional permission check for non-super-admin users
    if not current_user.is_super_admin and customer.club_id != current_user.club_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Cannot access customer from another club",
        )

    return customer
