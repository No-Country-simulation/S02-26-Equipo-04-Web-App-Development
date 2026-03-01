"""add ADD_AUDIO to JobType enums

Revision ID: 83979e9cb8d8
Revises: e7a3cf1c3a43
Create Date: 2026-02-28 18:28:21.548232

"""
from alembic import op
import sqlalchemy as sa


revision = '83979e9cb8d8'
down_revision = 'e7a3cf1c3a43'
branch_labels = None
depends_on = None


def upgrade():
    op.execute("ALTER TYPE jobtype ADD VALUE 'ADD_AUDIO'")


def downgrade() -> None:
    pass
