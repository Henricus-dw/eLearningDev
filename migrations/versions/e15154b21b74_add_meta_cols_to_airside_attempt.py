"""add meta cols to airside_attempt

Revision ID: e15154b21b74
Revises: a330c8e4a557
Create Date: 2025-08-17 14:31:52.778909

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'e15154b21b74'
down_revision = 'a330c8e4a557'
branch_labels = None
depends_on = None


def upgrade():
    # Columns were added manually via SQL. No-op.
    pass

def downgrade():
    # No-op (we’re not rolling these back on SQLite).
    pass