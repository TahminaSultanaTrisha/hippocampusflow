"""create scans table

Revision ID: 0002
Revises: 0001
"""
from alembic import op
import sqlalchemy as sa

revision = "0002"
down_revision = "0001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "scans",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("user_id", sa.String(36), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("image_key", sa.String(255), nullable=False),
        sa.Column("status", sa.String(20), nullable=False, server_default="uploaded"),
        sa.Column("category", sa.String(40), nullable=True),
        sa.Column("confidence", sa.Float(), nullable=True),
        sa.Column("summary", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_scans_user_created", "scans", ["user_id", "created_at"])


def downgrade() -> None:
    op.drop_index("ix_scans_user_created", table_name="scans")
    op.drop_table("scans")
