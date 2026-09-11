"""add company to student

Revision ID: 2e86a52fce15
Revises: 0bfb42d06b0e
Create Date: 2025-11-26 10:44:35.605899

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '2e86a52fce15'
down_revision = '0bfb42d06b0e'
branch_labels = None
depends_on = None


def upgrade():
    # Only add the company column + index on student
    with op.batch_alter_table('student', schema=None) as batch_op:
        batch_op.add_column(sa.Column('company', sa.String(length=120), nullable=True))
        batch_op.create_index('ix_student_company', ['company'], unique=False)


def downgrade():
    # Clean rollback: drop index + column
    with op.batch_alter_table('student', schema=None) as batch_op:
        batch_op.drop_index('ix_student_company')
        batch_op.drop_column('company')