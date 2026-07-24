"""add user role and display_name

Revision ID: 0002
Revises: 0001
Create Date: 2026-07-02

"""

from alembic import op
import sqlalchemy as sa


revision = "0002"
down_revision = "0001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("users", sa.Column("display_name", sa.String(length=128), nullable=True))
    op.add_column(
        "users",
        sa.Column("role", sa.String(length=32), nullable=False, server_default="youth"),
    )


def downgrade() -> None:
    op.drop_column("users", "role")
    op.drop_column("users", "display_name")
