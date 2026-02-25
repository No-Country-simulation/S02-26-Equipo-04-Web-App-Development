"""merge heads

Revision ID: ef638bd9753a
Revises: 2d022ca7669d, f14b135ae3cb
Create Date: 2026-02-24 15:23:07.709579

"""
from alembic import op
import sqlalchemy as sa


revision = 'ef638bd9753a'
down_revision = ('2d022ca7669d', 'f14b135ae3cb')
branch_labels = None
depends_on = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
