"""Add ProctorViolation table"""

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'd3dc55b32fd6'
down_revision = 'b31a0cc7d40b'
branch_labels = None
depends_on = None


def upgrade():
    # --- CREATE TABLE (only new table; do NOT touch other tables) ---
    op.create_table(
        'proctor_violations',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('student_id', sa.Integer(), nullable=True),                 # optional FK to student.id (not enforced in SQLite)
        sa.Column('student_number', sa.String(length=64), nullable=True),
        sa.Column('course_key', sa.String(length=64), nullable=True),
        sa.Column('reason', sa.String(length=255), nullable=False),
        sa.Column('ip', sa.String(length=64), nullable=True),
        sa.Column('user_agent', sa.String(length=256), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('extra_json', sa.Text(), nullable=True),
    )

    # Indexes for quick filtering
    op.create_index('ix_proctor_violations_student_number', 'proctor_violations', ['student_number'])
    op.create_index('ix_proctor_violations_course_key', 'proctor_violations', ['course_key'])
    op.create_index('ix_proctor_violations_created_at', 'proctor_violations', ['created_at'])


def downgrade():
    # Drop in reverse order
    op.drop_index('ix_proctor_violations_created_at', table_name='proctor_violations')
    op.drop_index('ix_proctor_violations_course_key', table_name='proctor_violations')
    op.drop_index('ix_proctor_violations_student_number', table_name='proctor_violations')
    op.drop_table('proctor_violations')