"""Agregar AUTO_REFRAME a job_type_enum

Revision ID: 3e8a83906bdf
Revises: 5a4f27fff629
Create Date: 2026-02-25 06:25:29.099555

"""
from alembic import op
import sqlalchemy as sa


revision = '3e8a83906bdf'
down_revision = '5a4f27fff629'
branch_labels = None
depends_on = None

# Nombre exacto del tipo ENUM en PostgreSQL
enum_name = 'jobtype'

def upgrade() -> None:
    # Agregar el nuevo valor al ENUM
    op.execute(f"ALTER TYPE {enum_name} ADD VALUE 'AUTO_REFRAME';")


def downgrade() -> None:
    pass
