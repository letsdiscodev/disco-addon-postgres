"""1.1.0 B

Revision ID: 01f55269072f
Revises: d49d80339efd
Create Date: 2025-01-28 01:43:53.385317

"""

import sqlalchemy as sa
from alembic import op

revision = "01f55269072f"
down_revision = "d49d80339efd"
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table("instances", schema=None) as batch_op:
        batch_op.alter_column(
            "image", existing_type=sa.VARCHAR(length=255), nullable=False
        )


def downgrade():
    with op.batch_alter_table("instances", schema=None) as batch_op:
        batch_op.alter_column(
            "image", existing_type=sa.VARCHAR(length=255), nullable=True
        )
