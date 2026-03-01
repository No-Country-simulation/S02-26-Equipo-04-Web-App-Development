"""add display_name to jobs

Revision ID: 9f8b7d3c2a11
Revises: 3e8a83906bdf
Create Date: 2026-03-01 13:10:00.000000

"""

from alembic import op
import sqlalchemy as sa


revision = "9f8b7d3c2a11"
down_revision = "3e8a83906bdf"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "jobs", sa.Column("display_name", sa.String(length=255), nullable=True)
    )


def downgrade() -> None:
    op.drop_column("jobs", "display_name")
