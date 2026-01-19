"""Change college and course to JSON arrays

Revision ID: 004
Revises: 003
Create Date: 2026-01-19 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
import json


# revision identifiers, used by Alembic.
revision: str = '004'
down_revision: Union[str, None] = '003'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # SQLite doesn't support ALTER COLUMN directly, so we need to:
    # 1. Create new columns
    # 2. Migrate data
    # 3. Drop old columns
    # 4. Rename new columns
    
    # Add new JSON columns
    op.add_column('applications', sa.Column('college_new', sa.JSON(), nullable=True))
    op.add_column('applications', sa.Column('course_new', sa.JSON(), nullable=True))
    
    # Migrate existing data - convert string to array with single element
    connection = op.get_bind()
    connection.execute(sa.text("""
        UPDATE applications 
        SET college_new = json_array(college),
            course_new = json_array(course)
    """))
    
    # Drop old columns (SQLite requires recreation of table)
    with op.batch_alter_table('applications') as batch_op:
        batch_op.drop_column('college')
        batch_op.drop_column('course')
    
    # Rename new columns to original names
    with op.batch_alter_table('applications') as batch_op:
        batch_op.alter_column('college_new', new_column_name='college', nullable=False)
        batch_op.alter_column('course_new', new_column_name='course', nullable=False)


def downgrade() -> None:
    # Reverse the process
    op.add_column('applications', sa.Column('college_old', sa.String(255), nullable=True))
    op.add_column('applications', sa.Column('course_old', sa.String(255), nullable=True))
    
    # Migrate data back - take first element of array
    connection = op.get_bind()
    connection.execute(sa.text("""
        UPDATE applications 
        SET college_old = json_extract(college, '$[0]'),
            course_old = json_extract(course, '$[0]')
    """))
    
    with op.batch_alter_table('applications') as batch_op:
        batch_op.drop_column('college')
        batch_op.drop_column('course')
    
    with op.batch_alter_table('applications') as batch_op:
        batch_op.alter_column('college_old', new_column_name='college', nullable=False)
        batch_op.alter_column('course_old', new_column_name='course', nullable=False)
