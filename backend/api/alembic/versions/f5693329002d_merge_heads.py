"""merge_heads

Revision ID: f5693329002d
Revises: 2d022ca7669d, f14b135ae3cb
Create Date: 2026-02-23 23:31:34.892112

"""
from alembic import op
import sqlalchemy as sa


revision = 'f5693329002d'
down_revision = ('2d022ca7669d', 'f14b135ae3cb')
branch_labels = None
depends_on = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
