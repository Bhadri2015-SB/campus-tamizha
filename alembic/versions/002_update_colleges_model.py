"""Update colleges model for AISHE data

Revision ID: 002
Revises: 001
Create Date: 2026-01-14 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '002'
down_revision: Union[str, None] = '001'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Drop old colleges table
    op.drop_table('colleges')
    
    # Create new colleges table with updated structure
    op.create_table('colleges',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('aishe_code', sa.String(length=50), nullable=False),
        sa.Column('name', sa.String(length=500), nullable=False),
        sa.Column('address', sa.Text(), nullable=True),
        sa.Column('state_name', sa.String(length=100), nullable=True),
        sa.Column('district_name', sa.String(length=100), nullable=True),
        sa.Column('website', sa.String(length=255), nullable=True),
        sa.Column('management', sa.String(length=100), nullable=True),
        sa.Column('year_of_establishment', sa.String(length=10), nullable=True),
        sa.Column('institution_type', sa.String(length=100), nullable=True),
        sa.Column('specialized_in', sa.String(length=255), nullable=True),
        sa.Column('university_id', sa.String(length=50), nullable=True),
        sa.Column('university_name', sa.String(length=255), nullable=True),
        sa.Column('university_type', sa.String(length=100), nullable=True),
        sa.Column('location', sa.String(length=50), nullable=True),
        sa.Column('active', sa.Boolean(), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create indexes for better query performance
    op.create_index(op.f('ix_colleges_aishe_code'), 'colleges', ['aishe_code'], unique=True)
    op.create_index(op.f('ix_colleges_name'), 'colleges', ['name'], unique=False)
    op.create_index(op.f('ix_colleges_district_name'), 'colleges', ['district_name'], unique=False)
    op.create_index(op.f('ix_colleges_university_name'), 'colleges', ['university_name'], unique=False)


def downgrade() -> None:
    # Drop new colleges table
    op.drop_index(op.f('ix_colleges_university_name'), table_name='colleges')
    op.drop_index(op.f('ix_colleges_district_name'), table_name='colleges')
    op.drop_index(op.f('ix_colleges_name'), table_name='colleges')
    op.drop_index(op.f('ix_colleges_aishe_code'), table_name='colleges')
    op.drop_table('colleges')
    
    # Recreate old colleges table
    op.create_table('colleges',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('city', sa.String(length=100), nullable=False),
        sa.Column('email', sa.String(length=255), nullable=False),
        sa.Column('whatsapp', sa.String(length=20), nullable=False),
        sa.Column('active', sa.Boolean(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('name')
    )
