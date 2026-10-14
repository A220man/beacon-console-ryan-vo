"""Initial schema

Revision ID: 001
Revises: 
Create Date: 2026-10-14
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = '001'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        'users',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('keycloak_sub', sa.String(length=255), nullable=False),
        sa.Column('email', sa.String(length=255), nullable=False),
        sa.Column('username', sa.String(length=255), nullable=False),
        sa.Column('full_name', sa.String(length=255), nullable=True),
        sa.Column('role', sa.Enum('viewer', 'operator', 'admin', name='userrole'), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False, default=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('last_login_at', sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('keycloak_sub'),
        sa.UniqueConstraint('email'),
        sa.UniqueConstraint('username'),
    )
    op.create_index('ix_users_email_active', 'users', ['email', 'is_active'], unique=False)
    op.create_index('ix_users_keycloak_sub', 'users', ['keycloak_sub'], unique=True)

    op.create_table(
        'skills',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('display_name', sa.String(length=255), nullable=False),
        sa.Column('description', sa.Text(), nullable=False),
        sa.Column('category', sa.Enum('genetics', 'ontology', 'literature', 'analysis', 'onboarding', 'other', name='skillcategory'), nullable=False, default='other'),
        sa.Column('status', sa.Enum('draft', 'validated', 'deprecated', name='skillstatus'), nullable=False, default='draft'),
        sa.Column('version', sa.String(length=50), nullable=False, default='1.0.0'),
        sa.Column('schema', sa.Text(), nullable=False),
        sa.Column('metadata_json', sa.Text(), nullable=False, default='{}'),
        sa.Column('owner_id', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.ForeignKeyConstraint(['owner_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('name'),
    )
    op.create_index('ix_skills_category_status', 'skills', ['category', 'status'], unique=False)
    op.create_index('ix_skills_owner_status', 'skills', ['owner_id', 'status'], unique=False)

    op.create_table(
        'executions',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('skill_id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('status', sa.Enum('pending', 'running', 'completed', 'failed', 'cancelled', name='executionstatus'), nullable=False, default='pending'),
        sa.Column('input_params', sa.Text(), nullable=False, default='{}'),
        sa.Column('output_result', sa.Text(), nullable=True),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('started_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.ForeignKeyConstraint(['skill_id'], ['skills.id'], ),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_executions_user_status', 'executions', ['user_id', 'status'], unique=False)
    op.create_index('ix_executions_skill_created', 'executions', ['skill_id', 'created_at'], unique=False)

    op.create_table(
        'audit_log',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=True),
        sa.Column('action', sa.String(length=100), nullable=False),
        sa.Column('resource_type', sa.String(length=50), nullable=False),
        sa.Column('resource_id', sa.String(length=50), nullable=True),
        sa.Column('details', sa.Text(), nullable=False, default='{}'),
        sa.Column('ip_address', sa.String(length=45), nullable=True),
        sa.Column('user_agent', sa.String(length=500), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_audit_user_resource', 'audit_log', ['user_id', 'resource_type', 'resource_id'], unique=False)
    op.create_index('ix_audit_created_action', 'audit_log', ['created_at', 'action'], unique=False)


def downgrade() -> None:
    op.drop_index('ix_audit_created_action', table_name='audit_log')
    op.drop_index('ix_audit_user_resource', table_name='audit_log')
    op.drop_table('audit_log')
    op.drop_index('ix_executions_skill_created', table_name='executions')
    op.drop_index('ix_executions_user_status', table_name='executions')
    op.drop_table('executions')
    op.drop_index('ix_skills_owner_status', table_name='skills')
    op.drop_index('ix_skills_category_status', table_name='skills')
    op.drop_table('skills')
    op.drop_index('ix_users_keycloak_sub', table_name='users')
    op.drop_index('ix_users_email_active', table_name='users')
    op.drop_table('users')

    op.execute('DROP TYPE IF EXISTS userrole')
    op.execute('DROP TYPE IF EXISTS skillcategory')
    op.execute('DROP TYPE IF EXISTS skillstatus')
    op.execute('DROP TYPE IF EXISTS executionstatus')