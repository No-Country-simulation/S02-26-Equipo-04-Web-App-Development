"""Update TimestampMixin to use timezone and server_default

Revision ID: a2b3c4d5e6f7_timestamp_tz
Revises: e7a3cf1c3a43
Create Date: 2026-02-28 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.sql import func


revision = 'a2b3c4d5e6f7_timestamp_tz'
down_revision = 'e7a3cf1c3a43'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Upgrade: Add timezone support and server defaults to all timestamp columns."""
    
    # List of tables that have created_at and updated_at columns
    tables = ['users', 'profiles', 'videos', 'audios', 'jobs', 'oauth_tokens']
    
    for table in tables:
        # Update created_at column
        op.alter_column(
            table, 'created_at',
            existing_type=sa.DateTime(),
            type_=sa.DateTime(timezone=True),
            existing_nullable=False,
            server_default=func.now(),
            existing_server_default=None,
        )
        
        # Update updated_at column
        op.alter_column(
            table, 'updated_at',
            existing_type=sa.DateTime(),
            type_=sa.DateTime(timezone=True),
            existing_nullable=False,
            server_default=func.now(),
            existing_server_default=None,
        )


def downgrade() -> None:
    """Downgrade: Revert timezone support and server defaults."""
    
    tables = ['users', 'profiles', 'videos', 'audios', 'jobs', 'oauth_tokens']
    
    for table in tables:
        # Revert created_at column
        op.alter_column(
            table, 'created_at',
            existing_type=sa.DateTime(timezone=True),
            type_=sa.DateTime(),
            existing_nullable=False,
            existing_server_default=func.now(),
            server_default=None,
        )
        
        # Revert updated_at column
        op.alter_column(
            table, 'updated_at',
            existing_type=sa.DateTime(timezone=True),
            type_=sa.DateTime(),
            existing_nullable=False,
            existing_server_default=func.now(),
            server_default=None,
        )
