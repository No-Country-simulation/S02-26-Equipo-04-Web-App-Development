"""crear tabla oauth_tokens

Revision ID: 6b7c8d9e0f1a
Revises: 5a4f27fff629
Create Date: 2026-02-26 11:30:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '6b7c8d9e0f1a'
down_revision = '5a4f27fff629'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Crear tabla oauth_tokens para almacenar tokens de servicios externos"""
    op.create_table(
        'oauth_tokens',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('provider', sa.String(), nullable=False),
        sa.Column('access_token', sa.Text(), nullable=False),
        sa.Column('refresh_token', sa.Text(), nullable=True),
        sa.Column('token_type', sa.String(), nullable=False, server_default='Bearer'),
        sa.Column('scope', sa.Text(), nullable=True),
        sa.Column('expires_at', sa.DateTime(), nullable=True),
        sa.Column('provider_user_id', sa.String(), nullable=True),
        sa.Column('provider_username', sa.String(), nullable=True),
        sa.Column('last_refreshed_at', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Índices para mejorar performance
    op.create_index('ix_oauth_tokens_user_id', 'oauth_tokens', ['user_id'])
    op.create_index('ix_oauth_tokens_provider', 'oauth_tokens', ['provider'])
    op.create_index('ix_oauth_tokens_user_provider', 'oauth_tokens', ['user_id', 'provider'], unique=True)


def downgrade() -> None:
    """Eliminar tabla oauth_tokens"""
    op.drop_index('ix_oauth_tokens_user_provider', table_name='oauth_tokens')
    op.drop_index('ix_oauth_tokens_provider', table_name='oauth_tokens')
    op.drop_index('ix_oauth_tokens_user_id', table_name='oauth_tokens')
    op.drop_table('oauth_tokens')
