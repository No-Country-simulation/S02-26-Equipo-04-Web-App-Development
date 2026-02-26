"""merge oauth_tokens y job_type_enum

Revision ID: cc43b98ae8fa
Revises: 3e8a83906bdf, 6b7c8d9e0f1a
Create Date: 2026-02-26 15:38:31.885118

"""
from alembic import op
import sqlalchemy as sa


revision = 'cc43b98ae8fa'
down_revision = ('3e8a83906bdf', '6b7c8d9e0f1a')
branch_labels = None
depends_on = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
