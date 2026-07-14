"""memories table

Revision ID: 0004
Revises: 0003
"""
from alembic import op
import sqlalchemy as sa

revision = "0004"
down_revision = "0003"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "memories",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("user_id", sa.String(36), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("scan_id", sa.String(36), sa.ForeignKey("scans.id"), nullable=True),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("source", sa.String(20), nullable=False, server_default="scan"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_memories_user", "memories", ["user_id"])


def downgrade() -> None:
    op.drop_index("ix_memories_user", table_name="memories")
    op.drop_table("memories")
