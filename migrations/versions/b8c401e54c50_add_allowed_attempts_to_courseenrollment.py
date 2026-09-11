from alembic import op
import sqlalchemy as sa

# Revision identifiers, used by Alembic.
revision = "b8c401e54c50"
down_revision = "2462e227eb09"
branch_labels = None
depends_on = None

def upgrade():
    # add with a server default so SQLite is happy
    with op.batch_alter_table("course_enrollment") as b:
        b.add_column(sa.Column("allowed_attempts", sa.Integer(),
                               nullable=False, server_default="3"))

    # optional: drop the server_default later (SQLite ignores this; others obey)
    if op.get_bind().dialect.name != "sqlite":
        op.alter_column("course_enrollment", "allowed_attempts", server_default=None)

def downgrade():
    with op.batch_alter_table("course_enrollment") as b:
        b.drop_column("allowed_attempts")