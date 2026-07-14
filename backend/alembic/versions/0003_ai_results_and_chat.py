"""scan_results and messages tables

Revision ID: 0003
Revises: 0002
"""
from alembic import op
import sqlalchemy as sa

revision = "0003"
down_revision = "0002"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "scan_results",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("scan_id", sa.String(36), sa.ForeignKey("scans.id"), nullable=False, unique=True),
        sa.Column("agent", sa.String(40), nullable=False),
        sa.Column("details_json", sa.Text(), nullable=False, server_default="{}"),
        sa.Column("actions_json", sa.Text(), nullable=False, server_default="[]"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_table(
        "messages",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("scan_id", sa.String(36), sa.ForeignKey("scans.id"), nullable=False),
        sa.Column("role", sa.String(10), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_messages_scan", "messages", ["scan_id"])


def downgrade() -> None:
    op.drop_index("ix_messages_scan", table_name="messages")
    op.drop_table("messages")
    op.drop_table("scan_results")
