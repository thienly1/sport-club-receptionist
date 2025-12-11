"""
Initial migration - Create all tables

Revision ID: 001_initial
Create Date: 2025-01-01 00:00:00.000000
"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# Revision identifiers
revision = "001_initial"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create all tables"""

    # Create clubs table
    op.create_table(
        "clubs",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("slug", sa.String(255), unique=True, nullable=False),
        sa.Column("email", sa.String(255), nullable=False, unique=True),
        sa.Column("phone", sa.String(20), nullable=False),
        sa.Column("address", sa.Text()),
        sa.Column("city", sa.String(100)),
        sa.Column("postal_code", sa.String(20)),
        sa.Column("country", sa.String(100), default="Sweden"),
        sa.Column("description", sa.Text()),
        sa.Column("website", sa.String(255)),
        sa.Column("matchi_club_id", sa.String(100)),
        sa.Column("matchi_booking_url", sa.String(500)),
        sa.Column("membership_types", postgresql.JSON(), default=[]),
        sa.Column("pricing_info", postgresql.JSON(), default={}),
        sa.Column("facilities", postgresql.JSON(), default=[]),
        sa.Column("opening_hours", postgresql.JSON(), default={}),
        sa.Column("policies", sa.Text()),
        sa.Column("ai_assistant_id", sa.String(100)),
        sa.Column("custom_greeting", sa.Text()),
        sa.Column("knowledge_base", postgresql.JSON(), default={}),
        sa.Column("vapi_phone_number", sa.String(20)),
        sa.Column("is_active", sa.Boolean(), default=True),
        sa.Column("subscription_tier", sa.String(50), default="basic"),
        sa.Column("manager_name", sa.String(255)),
        sa.Column("manager_phone", sa.String(20)),
        sa.Column("manager_email", sa.String(255)),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
    )

    # Create indexes for clubs
    op.create_index("ix_clubs_slug", "clubs", ["slug"])
    op.create_index("ix_clubs_matchi_club_id", "clubs", ["matchi_club_id"])

    # Create customers table
    op.create_table(
        "customers",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("club_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("phone", sa.String(20), nullable=False),
        sa.Column("email", sa.String(255)),
        sa.Column("source", sa.String(100)),
        sa.Column(
            "status",
            sa.Enum("lead", "interested", "trial", "member", "inactive", name="customerstatus"),
            nullable=False,
        ),
        sa.Column("interested_in", sa.Text()),
        sa.Column("membership_type_interest", sa.String(100)),
        sa.Column("preferred_contact_method", sa.String(50)),
        sa.Column("notes", sa.Text()),
        sa.Column("requires_follow_up", sa.Boolean(), default=False),
        sa.Column("follow_up_date", sa.DateTime()),
        sa.Column("is_high_priority", sa.Boolean(), default=False),
        sa.Column("converted_to_member", sa.Boolean(), default=False),
        sa.Column("conversion_date", sa.DateTime()),
        sa.Column("consent_marketing", sa.Boolean(), default=False),
        sa.Column("first_contact_date", sa.DateTime(), nullable=False),
        sa.Column("last_contact_date", sa.DateTime(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["club_id"], ["clubs.id"]),
    )

    # Create indexes for customers
    op.create_index("ix_customers_club_id", "customers", ["club_id"])
    op.create_index("ix_customers_phone", "customers", ["phone"])
    op.create_index("ix_customers_status", "customers", ["status"])

    # Create conversations table
    op.create_table(
        "conversations",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("club_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("customer_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("vapi_call_id", sa.String(255), unique=True),
        sa.Column("vapi_assistant_id", sa.String(255)),
        sa.Column("phone_number", sa.String(20)),
        sa.Column("call_duration", sa.Integer()),
        sa.Column("call_cost", sa.Float()),
        sa.Column(
            "status",
            sa.Enum("active", "completed", "escalated", "abandoned", name="conversationstatus"),
            nullable=False,
        ),
        sa.Column("intent", sa.String(255)),
        sa.Column("summary", sa.Text()),
        sa.Column("sentiment", sa.String(50)),
        sa.Column("topics_discussed", postgresql.JSON(), default=[]),
        sa.Column("questions_asked", postgresql.JSON(), default=[]),
        sa.Column("outcome", sa.String(100)),
        sa.Column("action_required", sa.Text()),
        sa.Column("escalated_to_manager", sa.Boolean(), default=False),
        sa.Column("customer_satisfaction", sa.Integer()),
        sa.Column("resolution_status", sa.String(50)),
        sa.Column("started_at", sa.DateTime(), nullable=False),
        sa.Column("ended_at", sa.DateTime()),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["club_id"], ["clubs.id"]),
        sa.ForeignKeyConstraint(["customer_id"], ["customers.id"]),
    )

    # Create indexes for conversations
    op.create_index("ix_conversations_club_id", "conversations", ["club_id"])
    op.create_index("ix_conversations_customer_id", "conversations", ["customer_id"])
    op.create_index("ix_conversations_vapi_call_id", "conversations", ["vapi_call_id"])
    op.create_index("ix_conversations_status", "conversations", ["status"])
    op.create_index("ix_conversations_started_at", "conversations", ["started_at"])

    # Create messages table
    op.create_table(
        "messages",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("conversation_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("role", sa.Enum("customer", "assistant", "system", name="messagerole"), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("timestamp", sa.DateTime(), nullable=False),
        sa.Column("duration", sa.Float()),
        sa.Column("vapi_message_id", sa.String(255)),
        sa.Column("function_call", postgresql.JSON()),
        sa.ForeignKeyConstraint(["conversation_id"], ["conversations.id"]),
    )

    # Create indexes for messages
    op.create_index("ix_messages_conversation_id", "messages", ["conversation_id"])
    op.create_index("ix_messages_timestamp", "messages", ["timestamp"])

    # Create bookings table
    op.create_table(
        "bookings",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("club_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("customer_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("conversation_id", postgresql.UUID(as_uuid=True)),
        sa.Column(
            "booking_type", sa.Enum("court", "coaching", "trial", "event", "other", name="bookingtype"), nullable=False
        ),
        sa.Column(
            "status",
            sa.Enum("pending", "confirmed", "completed", "cancelled", "no_show", name="bookingstatus"),
            nullable=False,
        ),
        sa.Column("resource_name", sa.String(255)),
        sa.Column("description", sa.Text()),
        sa.Column("booking_date", sa.DateTime(), nullable=False),
        sa.Column("start_time", sa.DateTime(), nullable=False),
        sa.Column("end_time", sa.DateTime(), nullable=False),
        sa.Column("duration_minutes", sa.Integer()),
        sa.Column("price", sa.Float()),
        sa.Column("currency", sa.String(10), default="SEK"),
        sa.Column("payment_status", sa.String(50)),
        sa.Column("contact_name", sa.String(255)),
        sa.Column("contact_phone", sa.String(20)),
        sa.Column("contact_email", sa.String(255)),
        sa.Column("notes", sa.Text()),
        sa.Column("special_requests", sa.Text()),
        sa.Column("matchi_booking_id", sa.String(100)),
        sa.Column("synced_to_matchi", sa.DateTime()),
        sa.Column("confirmation_code", sa.String(50), unique=True),
        sa.Column("confirmation_sent_at", sa.DateTime()),
        sa.Column("cancellation_reason", sa.Text()),
        sa.Column("cancelled_at", sa.DateTime()),
        sa.Column("cancelled_by", sa.String(100)),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["club_id"], ["clubs.id"]),
        sa.ForeignKeyConstraint(["customer_id"], ["customers.id"]),
        sa.ForeignKeyConstraint(["conversation_id"], ["conversations.id"]),
    )

    # Create indexes for bookings
    op.create_index("ix_bookings_club_id", "bookings", ["club_id"])
    op.create_index("ix_bookings_customer_id", "bookings", ["customer_id"])
    op.create_index("ix_bookings_status", "bookings", ["status"])
    op.create_index("ix_bookings_booking_date", "bookings", ["booking_date"])

    # Create notifications table
    op.create_table(
        "notifications",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("club_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("customer_id", postgresql.UUID(as_uuid=True)),
        sa.Column("conversation_id", postgresql.UUID(as_uuid=True)),
        sa.Column("booking_id", postgresql.UUID(as_uuid=True)),
        sa.Column(
            "notification_type",
            sa.Enum(
                "escalation",
                "booking_confirmation",
                "booking_reminder",
                "booking_cancellation",
                "lead_alert",
                "follow_up_reminder",
                "system_alert",
                name="notificationtype",
            ),
            nullable=False,
        ),
        sa.Column("channel", sa.Enum("sms", "email", "webhook", "push", name="notificationchannel"), nullable=False),
        sa.Column(
            "status",
            sa.Enum("pending", "sent", "delivered", "failed", "bounced", name="notificationstatus"),
            nullable=False,
        ),
        sa.Column("recipient_name", sa.String(255)),
        sa.Column("recipient_phone", sa.String(20)),
        sa.Column("recipient_email", sa.String(255)),
        sa.Column("subject", sa.String(255)),
        sa.Column("message", sa.Text(), nullable=False),
        sa.Column("template_used", sa.String(100)),
        sa.Column("context_data", postgresql.JSON(), default={}),
        sa.Column("provider", sa.String(50)),
        sa.Column("provider_message_id", sa.String(255)),
        sa.Column("provider_status", sa.String(50)),
        sa.Column("provider_response", postgresql.JSON()),
        sa.Column("sent_at", sa.DateTime()),
        sa.Column("delivered_at", sa.DateTime()),
        sa.Column("failed_at", sa.DateTime()),
        sa.Column("error_message", sa.Text()),
        sa.Column("retry_count", sa.Integer(), default=0),
        sa.Column("max_retries", sa.Integer(), default=3),
        sa.Column("next_retry_at", sa.DateTime()),
        sa.Column("cost", sa.Float()),
        sa.Column("currency", sa.String(10), default="SEK"),
        sa.Column("priority", sa.String(20), default="normal"),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["club_id"], ["clubs.id"]),
        sa.ForeignKeyConstraint(["customer_id"], ["customers.id"]),
        sa.ForeignKeyConstraint(["conversation_id"], ["conversations.id"]),
        sa.ForeignKeyConstraint(["booking_id"], ["bookings.id"]),
    )

    # Create indexes for notifications
    op.create_index("ix_notifications_club_id", "notifications", ["club_id"])
    op.create_index("ix_notifications_type", "notifications", ["notification_type"])
    op.create_index("ix_notifications_status", "notifications", ["status"])
    op.create_index("ix_notifications_created_at", "notifications", ["created_at"])


def downgrade() -> None:
    """Drop all tables"""
    op.drop_table("notifications")
    op.drop_table("bookings")
    op.drop_table("messages")
    op.drop_table("conversations")
    op.drop_table("customers")
    op.drop_table("clubs")

    # Drop enums
    op.execute("DROP TYPE IF EXISTS notificationstatus")
    op.execute("DROP TYPE IF EXISTS notificationchannel")
    op.execute("DROP TYPE IF EXISTS notificationtype")
    op.execute("DROP TYPE IF EXISTS bookingstatus")
    op.execute("DROP TYPE IF EXISTS bookingtype")
    op.execute("DROP TYPE IF EXISTS messagerole")
    op.execute("DROP TYPE IF EXISTS conversationstatus")
    op.execute("DROP TYPE IF EXISTS customerstatus")
