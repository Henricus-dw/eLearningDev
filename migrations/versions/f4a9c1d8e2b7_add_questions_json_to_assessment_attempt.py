"""Add question snapshots to assessment attempts.

Revision ID: f4a9c1d8e2b7
Revises: df527e262e9e
Create Date: 2026-09-11 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


revision = "f4a9c1d8e2b7"
down_revision = ("df527e262e9e", "79052f0914f3")
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table("assessment_attempt", schema=None) as batch_op:
        batch_op.add_column(
            sa.Column("questions_json", sa.Text(), nullable=True)
        )


def downgrade():
    with op.batch_alter_table("assessment_attempt", schema=None) as batch_op:
        batch_op.drop_column("questions_json")
