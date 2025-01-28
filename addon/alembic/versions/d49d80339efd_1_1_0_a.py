"""1.1.0 A

Revision ID: d49d80339efd
Revises: 53fa126b65b8
Create Date: 2025-01-28 01:42:37.441161

"""

import sqlalchemy as sa
from alembic import op

revision = "d49d80339efd"
down_revision = "53fa126b65b8"
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table("instances", schema=None) as batch_op:
        batch_op.add_column(sa.Column("image", sa.String(length=255), nullable=True))


def downgrade():
    with op.batch_alter_table("instances", schema=None) as batch_op:
        batch_op.drop_column("image")
