"""
Add users table for authentication

Revision ID: 002_add_users
Revises: 001_initial
Create Date: 2025-01-15 00:00:00.000000
"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# Revision identifiers
revision = "002_add_users"
down_revision = "001_initial"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Add users table"""

    # Create users table
    op.create_table(
        "users",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("club_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("email", sa.String(255), nullable=False, unique=True),
        sa.Column("username", sa.String(100), nullable=False, unique=True),
        sa.Column("hashed_password", sa.String(255), nullable=False),
        sa.Column("full_name", sa.String(255), nullable=False),
        sa.Column("phone", sa.String(20)),
        sa.Column(
            "role", sa.Enum("super_admin", "club_admin", "club_staff", "viewer", name="userrole"), nullable=False
        ),
        sa.Column("is_active", sa.Boolean(), nullable=False, default=True),
        sa.Column("is_verified", sa.Boolean(), nullable=False, default=False),
        sa.Column("last_login", sa.DateTime()),
        sa.Column("last_password_change", sa.DateTime(), nullable=False),
        sa.Column("failed_login_attempts", sa.Integer(), default=0),
        sa.Column("locked_until", sa.DateTime()),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["club_id"], ["clubs.id"], ondelete="SET NULL"),
    )

    # Create indexes for users table
    op.create_index("ix_users_email", "users", ["email"])
    op.create_index("ix_users_username", "users", ["username"])
    op.create_index("ix_users_club_id", "users", ["club_id"])
    op.create_index("ix_users_role", "users", ["role"])
    op.create_index("ix_users_is_active", "users", ["is_active"])


def downgrade() -> None:
    """Drop users table"""
    op.drop_table("users")

    # Drop enum
    op.execute("DROP TYPE IF EXISTS userrole")
