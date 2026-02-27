"""job output_path to JSON

Revision ID: 57e342f63517
Revises: 3e8a83906bdf
Create Date: 2026-02-26 19:09:31.912778

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = '57e342f63517'
down_revision = '3e8a83906bdf'
branch_labels = None
depends_on = None


def upgrade():
    # Para DB vacía, igual hay que usar USING cast
    op.execute("""
        ALTER TABLE jobs
        ALTER COLUMN output_path TYPE JSON
        USING '{}'::json
    """)

def downgrade():
    op.alter_column(
        'jobs',
        'output_path',
        type_=sa.String(500),
        existing_nullable=True
    )
