"""1.0.0

Revision ID: 53fa126b65b8
Revises:
Create Date: 2024-06-01 19:19:14.322889

"""

import sqlalchemy as sa
from alembic import op

revision = "53fa126b65b8"
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "instances",
        sa.Column("id", sa.String(length=32), nullable=False),
        sa.Column("created", sa.DateTime(), nullable=False),
        sa.Column("updated", sa.DateTime(), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("version", sa.String(length=255), nullable=False),
        sa.Column("admin_user", sa.String(length=255), nullable=False),
        sa.Column("admin_password", sa.String(length=255), nullable=False),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_instances")),
    )
    op.create_table(
        "key_values",
        sa.Column("key", sa.String(length=255), nullable=False),
        sa.Column("created", sa.DateTime(), nullable=False),
        sa.Column("updated", sa.DateTime(), nullable=False),
        sa.Column("value", sa.UnicodeText(), nullable=True),
        sa.PrimaryKeyConstraint("key", name=op.f("pk_key_values")),
    )
    op.create_table(
        "databases",
        sa.Column("id", sa.String(length=32), nullable=False),
        sa.Column("created", sa.DateTime(), nullable=False),
        sa.Column("updated", sa.DateTime(), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("instance_id", sa.String(length=32), nullable=False),
        sa.ForeignKeyConstraint(
            ["instance_id"],
            ["instances.id"],
            name=op.f("fk_databases_instance_id_instances"),
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_databases")),
    )
    with op.batch_alter_table("databases", schema=None) as batch_op:
        batch_op.create_index(
            batch_op.f("ix_databases_instance_id"), ["instance_id"], unique=False
        )

    op.create_table(
        "users",
        sa.Column("id", sa.String(length=32), nullable=False),
        sa.Column("created", sa.DateTime(), nullable=False),
        sa.Column("updated", sa.DateTime(), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("password", sa.String(length=255), nullable=False),
        sa.Column("database_id", sa.String(length=32), nullable=False),
        sa.ForeignKeyConstraint(
            ["database_id"],
            ["databases.id"],
            name=op.f("fk_users_database_id_databases"),
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_users")),
    )
    with op.batch_alter_table("users", schema=None) as batch_op:
        batch_op.create_index(
            batch_op.f("ix_users_database_id"), ["database_id"], unique=False
        )

    op.create_table(
        "attachments",
        sa.Column("id", sa.String(length=32), nullable=False),
        sa.Column("created", sa.DateTime(), nullable=False),
        sa.Column("updated", sa.DateTime(), nullable=False),
        sa.Column("project_name", sa.String(length=255), nullable=False),
        sa.Column("env_var", sa.String(length=255), nullable=False),
        sa.Column("user_id", sa.String(length=32), nullable=False),
        sa.ForeignKeyConstraint(
            ["user_id"], ["users.id"], name=op.f("fk_attachments_user_id_users")
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_attachments")),
    )
    with op.batch_alter_table("attachments", schema=None) as batch_op:
        batch_op.create_index(
            batch_op.f("ix_attachments_user_id"), ["user_id"], unique=False
        )


def downgrade():
    with op.batch_alter_table("attachments", schema=None) as batch_op:
        batch_op.drop_index(batch_op.f("ix_attachments_user_id"))

    op.drop_table("attachments")
    with op.batch_alter_table("users", schema=None) as batch_op:
        batch_op.drop_index(batch_op.f("ix_users_database_id"))

    op.drop_table("users")
    with op.batch_alter_table("databases", schema=None) as batch_op:
        batch_op.drop_index(batch_op.f("ix_databases_instance_id"))

    op.drop_table("databases")
    op.drop_table("key_values")
    op.drop_table("instances")
