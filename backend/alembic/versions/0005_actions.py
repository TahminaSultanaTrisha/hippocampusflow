"""actions table

Revision ID: 0005
Revises: 0004
"""
from alembic import op
import sqlalchemy as sa

revision = "0005"
down_revision = "0004"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "actions",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("user_id", sa.String(36), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("scan_id", sa.String(36), sa.ForeignKey("scans.id"), nullable=False),
        sa.Column("action_type", sa.String(30), nullable=False),
        sa.Column("payload_json", sa.Text(), nullable=False, server_default="{}"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_actions_user", "actions", ["user_id"])


def downgrade() -> None:
    op.drop_index("ix_actions_user", table_name="actions")
    op.drop_table("actions")
