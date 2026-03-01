"""Merge heads after rebase

Revision ID: bdeb79f4d4e9
Revises: 83979e9cb8d8, a2b3c4d5e6f7_timestamp_tz
Create Date: 2026-03-01 10:41:37.608394

"""
from alembic import op
import sqlalchemy as sa


revision = 'bdeb79f4d4e9'
down_revision = ('83979e9cb8d8', 'a2b3c4d5e6f7_timestamp_tz')
branch_labels = None
depends_on = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
