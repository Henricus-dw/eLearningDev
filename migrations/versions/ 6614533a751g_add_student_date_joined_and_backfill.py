"""add student.date_joined and backfill"""

revision = "6614533a751g"
down_revision = "10b971a57a23"
branch_labels = None
depends_on = None

from alembic import op
import sqlalchemy as sa

def upgrade():
    # 1) Add as NULLable (SQLite-friendly)
    with op.batch_alter_table("student", schema=None) as batch_op:
        batch_op.add_column(sa.Column("date_joined", sa.DateTime(), nullable=True))

    # 2) Backfill from registration_date (fallback to now if needed)
    conn = op.get_bind()
    conn.execute(sa.text("""
        UPDATE student
        SET date_joined = COALESCE(registration_date, CURRENT_TIMESTAMP)
    """))

    # 3) Enforce NOT NULL + add index
    with op.batch_alter_table("student", schema=None) as batch_op:
        batch_op.alter_column("date_joined", existing_type=sa.DateTime(), nullable=False)
        batch_op.create_index(batch_op.f("ix_student_date_joined"), ["date_joined"], unique=False)

def downgrade():
    with op.batch_alter_table("student", schema=None) as batch_op:
        batch_op.drop_index(batch_op.f("ix_student_date_joined"))
        batch_op.drop_column("date_joined")