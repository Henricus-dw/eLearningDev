from alembic import op
import sqlalchemy as sa

revision = '0a30796d7c27'
down_revision = '67862fffaad6'
branch_labels = None
depends_on = None

def upgrade():
    bind = op.get_bind()
    insp = sa.inspect(bind)
    cols = [c['name'] for c in insp.get_columns('course')]
    if 'cover_image' not in cols:
        op.add_column('course', sa.Column('cover_image', sa.String(length=255), nullable=True))

def downgrade():
    bind = op.get_bind()
    insp = sa.inspect(bind)
    cols = [c['name'] for c in insp.get_columns('course')]
    if 'cover_image' in cols:
        op.drop_column('course', 'cover_image')