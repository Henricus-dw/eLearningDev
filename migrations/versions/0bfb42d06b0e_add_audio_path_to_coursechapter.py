"""Add audio_path to CourseChapter

Revision ID: 0bfb42d06b0e
Revises: 5834d20bfc79
Create Date: 2025-11-19 13:17:45.266972
"""
from alembic import op
import sqlalchemy as sa

revision = '0bfb42d06b0e'
down_revision = '5834d20bfc79'
branch_labels = None
depends_on = None


def upgrade():
    # ✅ Only add audio_path to course_chapter
    with op.batch_alter_table('course_chapter', schema=None) as batch_op:
        batch_op.add_column(sa.Column('audio_path', sa.String(length=255), nullable=True))


def downgrade():
    # ✅ Only remove audio_path on downgrade
    with op.batch_alter_table('course_chapter', schema=None) as batch_op:
        batch_op.drop_column('audio_path')