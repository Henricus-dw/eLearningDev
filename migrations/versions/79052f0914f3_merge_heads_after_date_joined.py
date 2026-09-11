"""merge heads after date_joined

Revision ID: 79052f0914f3
Revises: 6614533a751f, 6614533a751g
Create Date: 2025-09-26 09:14:43.412889

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '79052f0914f3'
down_revision = ('6614533a751f', '6614533a751g')
branch_labels = None
depends_on = None


def upgrade():
    pass


def downgrade():
    pass
