"""Enable ON DELETE CASCADE for course_id in FinalAssessmentSubmission

Revision ID: 7464d94bb281
Revises: c2df6e5414b5
Create Date: 2025-04-08 12:51:15.121493
"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '7464d94bb281'
down_revision = 'c2df6e5414b5'
branch_labels = None
depends_on = None


def upgrade():
    # Rename existing table to preserve old data
    op.rename_table('final_assessment_submission', 'final_assessment_submission_old')

    # Recreate table with ON DELETE CASCADE
    op.create_table(
        'final_assessment_submission',
        sa.Column('id', sa.Integer, primary_key=True),
        sa.Column('student_id', sa.Integer, sa.ForeignKey('student.id'), nullable=False),
        sa.Column('course_id', sa.Integer, sa.ForeignKey('course.id', ondelete='CASCADE'), nullable=False),
        sa.Column('video_filename', sa.String(length=255), nullable=False),
        sa.Column('score', sa.Integer),
        sa.Column('total_questions', sa.Integer),
        sa.Column('percentage', sa.Float),
        sa.Column('review_status', sa.String(length=50), nullable=False, server_default="Pending"),
        sa.Column('submitted_at', sa.DateTime, server_default=sa.func.now())
    )

    # Insert only valid rows with course_id that exists
    op.execute("""
        INSERT INTO final_assessment_submission (
            id, student_id, course_id, video_filename,
            score, total_questions, percentage,
            review_status, submitted_at
        )
        SELECT
            fas.id, fas.student_id, fas.course_id, fas.video_filename,
            fas.score, fas.total_questions, fas.percentage,
            fas.review_status, fas.submitted_at
        FROM final_assessment_submission_old fas
        WHERE course_id IN (SELECT id FROM course)
    """)

    # Optional: Save invalid data for review
    op.execute("""
        CREATE TABLE IF NOT EXISTS orphaned_final_submissions AS
        SELECT * FROM final_assessment_submission_old
        WHERE course_id NOT IN (SELECT id FROM course)
    """)

    # Drop the old table
    op.drop_table('final_assessment_submission_old')


def downgrade():
    # Rename current table
    op.rename_table('final_assessment_submission', 'final_assessment_submission_new')

    # Recreate old version without ON DELETE CASCADE
    op.create_table(
        'final_assessment_submission',
        sa.Column('id', sa.Integer, primary_key=True),
        sa.Column('student_id', sa.Integer, sa.ForeignKey('student.id'), nullable=False),
        sa.Column('course_id', sa.Integer, sa.ForeignKey('course.id'), nullable=False),
        sa.Column('video_filename', sa.String(length=255), nullable=False),
        sa.Column('score', sa.Integer),
        sa.Column('total_questions', sa.Integer),
        sa.Column('percentage', sa.Float),
        sa.Column('review_status', sa.String(length=50), nullable=False, server_default="Pending"),
        sa.Column('submitted_at', sa.DateTime, server_default=sa.func.now())
    )

    # Copy valid rows back
    op.execute("""
        INSERT INTO final_assessment_submission (
            id, student_id, course_id, video_filename,
            score, total_questions, percentage,
            review_status, submitted_at
        )
        SELECT
            id, student_id, course_id, video_filename,
            score, total_questions, percentage,
            review_status, submitted_at
        FROM final_assessment_submission_new
    """)

    op.drop_table('final_assessment_submission_new')