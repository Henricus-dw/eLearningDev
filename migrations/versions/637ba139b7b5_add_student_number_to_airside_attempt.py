"""add student_number to airside_attempt

Revision ID: 637ba139b7b5
Revises: e15154b21b74
Create Date: 2025-08-17 14:35:10.186475

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '637ba139b7b5'
down_revision = 'e15154b21b74'
branch_labels = None
depends_on = None


def upgrade():
    # Columns were added manually via SQL. No-op.
    pass

def downgrade():
    # No-op (we’re not rolling these back on SQLite).
    pass
    # ### end Alembic commands ###
