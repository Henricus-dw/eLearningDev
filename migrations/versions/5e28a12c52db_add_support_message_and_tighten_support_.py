from alembic import op
import sqlalchemy as sa

revision = "5e28a12c52db"
down_revision = "0a30796d7c27"
branch_labels = None
depends_on = None


def upgrade():
    bind = op.get_bind()
    insp = sa.inspect(bind)

    # 1) Nuke the leftover SQLite batch table if it exists
    op.execute("DROP TABLE IF EXISTS _alembic_tmp_violation_log")

    # 2) Create support_message only if it doesn't exist
    tables = set(insp.get_table_names())
    if "support_message" not in tables:
        op.create_table(
            "support_message",
            sa.Column("id", sa.Integer, primary_key=True),
            sa.Column(
                "ticket_id",
                sa.Integer,
                sa.ForeignKey("support_ticket.id", ondelete="CASCADE"),
                nullable=False,
            ),
            sa.Column("author_type", sa.String(20), nullable=False),
            sa.Column("author_email", sa.String(120), nullable=True),
            sa.Column(
                "created_at",
                sa.DateTime,
                nullable=False,
                server_default=sa.text("(CURRENT_TIMESTAMP)"),
            ),
            sa.Column("body", sa.Text, nullable=False),
        )
        op.create_index(
            "ix_support_message_ticket_created",
            "support_message",
            ["ticket_id", "created_at"],
            unique=False,
        )
    else:
        # 2a) Table exists. Only add anything missing (no data loss).
        existing_cols = {c["name"] for c in insp.get_columns("support_message")}
        # author_type
        if "author_type" not in existing_cols:
            op.add_column(
                "support_message",
                sa.Column("author_type", sa.String(20), nullable=False, server_default="admin"),
            )
            # drop the default after backfilling existing rows
            with op.batch_alter_table("support_message") as batch:
                batch.alter_column("author_type", server_default=None)

        # author_email
        if "author_email" not in existing_cols:
            op.add_column(
                "support_message",
                sa.Column("author_email", sa.String(120), nullable=True),
            )

        # body
        if "body" not in existing_cols:
            op.add_column("support_message", sa.Column("body", sa.Text, nullable=False, server_default=""))
            with op.batch_alter_table("support_message") as batch:
                batch.alter_column("body", server_default=None)

        # created_at
        if "created_at" not in existing_cols:
            op.add_column(
                "support_message",
                sa.Column(
                    "created_at",
                    sa.DateTime,
                    nullable=False,
                    server_default=sa.text("(CURRENT_TIMESTAMP)"),
                ),
            )
            with op.batch_alter_table("support_message") as batch:
                batch.alter_column("created_at", server_default=None)

        # index on (ticket_id, created_at)
        existing_indexes = {ix["name"] for ix in insp.get_indexes("support_message")}
        if "ix_support_message_ticket_created" not in existing_indexes:
            op.create_index(
                "ix_support_message_ticket_created",
                "support_message",
                ["ticket_id", "created_at"],
                unique=False,
            )

    # 3) Make violation_log tweaks idempotent and safe on existing data
    if "violation_log" in tables:
        # Ensure NOT NULL 'timestamp' and reasonable 'reason' width with default only during migration
        with op.batch_alter_table("violation_log") as batch:
            # Add a temporary default so SQLite can copy rows, then remove it
            batch.alter_column("timestamp", existing_type=sa.DateTime(), nullable=False)

            # If 'reason' exists, tighten type and ensure not null with a temp default
            existing_cols = {c["name"]: c for c in insp.get_columns("violation_log")}
            if "reason" in existing_cols:
                batch.alter_column(
                    "reason",
                    existing_type=sa.String(length=existing_cols["reason"].get("type", sa.String(200)).length or 200),
                    type_=sa.String(length=128),
                    nullable=False,
                    server_default="unknown",
                )
        # Drop the temporary default for reason
        with op.batch_alter_table("violation_log") as batch:
            batch.alter_column("reason", server_default=None)

        # Create indexes if missing
        existing_ix = {ix["name"] for ix in insp.get_indexes("violation_log")}
        if "ix_violation_log_course_key" not in existing_ix:
            op.create_index("ix_violation_log_course_key", "violation_log", ["course_key"], unique=False)
        if "ix_violation_log_reason" not in existing_ix:
            op.create_index("ix_violation_log_reason", "violation_log", ["reason"], unique=False)
        if "ix_violation_log_student_id" not in existing_ix:
            op.create_index("ix_violation_log_student_id", "violation_log", ["student_id"], unique=False)
        if "ix_violation_log_timestamp" not in existing_ix:
            op.create_index("ix_violation_log_timestamp", "violation_log", ["timestamp"], unique=False)


def downgrade():
    bind = op.get_bind()
    insp = sa.inspect(bind)

    # Best-effort reversible bits that won’t drop data accidentally
    if "violation_log" in insp.get_table_names():
        existing_ix = {ix["name"] for ix in insp.get_indexes("violation_log")}
        for name in [
            "ix_violation_log_timestamp",
            "ix_violation_log_student_id",
            "ix_violation_log_reason",
            "ix_violation_log_course_key",
        ]:
            if name in existing_ix:
                op.drop_index(name, table_name="violation_log")

        # Loosen reason type back if you insist
        with op.batch_alter_table("violation_log") as batch:
            batch.alter_column("reason", type_=sa.String(length=200), existing_nullable=False)

    if "support_message" in insp.get_table_names():
        # Only drop if you truly want to roll back the table
        op.drop_index("ix_support_message_ticket_created", table_name="support_message")
        op.drop_table("support_message")