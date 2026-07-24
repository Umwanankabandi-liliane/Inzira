"""add notify columns to saved_sites

Revision ID: 0003
Revises: 0002
Create Date: 2026-07-02

"""

from alembic import op
import sqlalchemy as sa


revision = "0003"
down_revision = "0002"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "saved_sites",
        sa.Column("notify_enabled", sa.Boolean(), nullable=False, server_default=sa.false()),
    )
    op.add_column("saved_sites", sa.Column("last_deadline", sa.String(length=128), nullable=True))
    op.add_column("saved_sites", sa.Column("last_deadline_check", sa.DateTime(timezone=True), nullable=True))


def downgrade() -> None:
    op.drop_column("saved_sites", "last_deadline_check")
    op.drop_column("saved_sites", "last_deadline")
    op.drop_column("saved_sites", "notify_enabled")
