"""merge migration heads

Revision ID: e7a3cf1c3a43
Revises: c18db94c4cef, cc43b98ae8fa
Create Date: 2026-02-28 17:56:24.411670

"""
from alembic import op
import sqlalchemy as sa


revision = 'e7a3cf1c3a43'
down_revision = ('c18db94c4cef', 'cc43b98ae8fa')
branch_labels = None
depends_on = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
