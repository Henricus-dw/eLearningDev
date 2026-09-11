from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "3e823b45369d"
down_revision = "4dbbdb513559"  # <- previous migration id (the one that created the table)
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table('final_assessment_attempts', schema=None) as batch_op:
        # give the constraint a name
        batch_op.create_foreign_key(
            'fk_final_assessment_attempts_course_id',  # <-- name required
            'course',
            ['course_id'],
            ['id'],
            ondelete='SET NULL'
        )

def downgrade():
    with op.batch_alter_table('final_assessment_attempts', schema=None) as batch_op:
        batch_op.drop_constraint(
            'fk_final_assessment_attempts_course_id',
            type_='foreignkey'
        )