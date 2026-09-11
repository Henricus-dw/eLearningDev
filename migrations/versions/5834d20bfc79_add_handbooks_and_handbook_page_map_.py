"""add handbooks and handbook_page_map tables

Revision ID: 5834d20bfc79
Revises: 5e28a12c52db
Create Date: 2025-11-07 10:16:56.985227
"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "5834d20bfc79"
down_revision = "5e28a12c52db"
branch_labels = None
depends_on = None


def upgrade():
    # --- handbooks ---
    op.create_table(
        "handbooks",
        sa.Column("id", sa.Integer(), primary_key=True, nullable=False),
        # make nullable=True so we can create the table even if course FK gets added later
        sa.Column("course_id", sa.Integer(), nullable=True),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("pdf_filename", sa.String(length=512), nullable=False),
        sa.Column("version", sa.String(length=64), nullable=True),
        sa.Column(
            "published_at",
            sa.DateTime(),
            nullable=False,
            server_default=sa.text("(CURRENT_TIMESTAMP)")
        ),
        sa.Column(
            "is_active",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("1")
        ),
    )
    op.create_index("ix_handbooks_course_id", "handbooks", ["course_id"], unique=False)
    op.create_index("ix_handbooks_is_active", "handbooks", ["is_active"], unique=False)

    # add FK to the real course table name
    bind = op.get_bind()
    insp = sa.inspect(bind)
    tables = set(insp.get_table_names())
    # Your app uses 'course' (you saw the autogen try to use course.id)
    target_course_table = "course" if "course" in tables else ("courses" if "courses" in tables else None)
    if target_course_table:
        op.create_foreign_key(
            "fk_handbooks_course",
            source_table="handbooks",
            referent_table=target_course_table,
            local_cols=["course_id"],
            remote_cols=["id"],
            ondelete="SET NULL",
        )

    # --- handbook_page_map ---
    op.create_table(
        "handbook_page_map",
        sa.Column("id", sa.Integer(), primary_key=True, nullable=False),
        sa.Column("handbook_id", sa.Integer(), nullable=False),
        sa.Column("chapter_key", sa.String(length=128), nullable=False),
        sa.Column("page_start", sa.Integer(), nullable=False),
        sa.Column("page_end", sa.Integer(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(),
            nullable=False,
            server_default=sa.text("(CURRENT_TIMESTAMP)")
        ),
    )
    op.create_index(
        "ix_handbook_page_map_handbook_id",
        "handbook_page_map",
        ["handbook_id"],
        unique=False,
    )
    op.create_index(
        "ix_handbook_page_map_chapter_key",
        "handbook_page_map",
        ["chapter_key"],
        unique=False,
    )
    op.create_foreign_key(
        "fk_handbook_page_map_handbook",
        source_table="handbook_page_map",
        referent_table="handbooks",
        local_cols=["handbook_id"],
        remote_cols=["id"],
        ondelete="CASCADE",
    )


def downgrade():
    # Drop in reverse dependency order
    op.drop_constraint("fk_handbook_page_map_handbook", "handbook_page_map", type_="foreignkey")
    op.drop_index("ix_handbook_page_map_chapter_key", table_name="handbook_page_map")
    op.drop_index("ix_handbook_page_map_handbook_id", table_name="handbook_page_map")
    op.drop_table("handbook_page_map")

    # handbooks
    try:
        op.drop_constraint("fk_handbooks_course", "handbooks", type_="foreignkey")
    except Exception:
        pass
    op.drop_index("ix_handbooks_is_active", table_name="handbooks")
    op.drop_index("ix_handbooks_course_id", table_name="handbooks")
    op.drop_table("handbooks")