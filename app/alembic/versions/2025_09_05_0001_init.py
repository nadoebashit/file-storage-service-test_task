"""init schema

Revision ID: 0001_init
Revises:
Create Date: 2025-09-05 00:00:00
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers
revision = "0001_init"
down_revision = None
branch_labels = None
depends_on = None

def upgrade() -> None:
    op.create_table(
        "departments",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.UniqueConstraint("name"),
    )
    op.create_index("ix_departments_name", "departments", ["name"])

    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("email", sa.String(length=255), nullable=False),
        sa.Column("password_hash", sa.String(length=255), nullable=False),
        sa.Column("role", sa.Enum("USER", "MANAGER", "ADMIN", name="userrole"), nullable=False, server_default="USER"),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("department_id", sa.Integer(), sa.ForeignKey("departments.id"), nullable=False),
    )
    op.create_index("ix_users_email", "users", ["email"], unique=True)
    op.create_index("ix_users_role", "users", ["role"])
    op.create_index("ix_users_department_id", "users", ["department_id"])

    op.create_table(
        "files",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("owner_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("department_id", sa.Integer(), sa.ForeignKey("departments.id"), nullable=False),
        sa.Column("filename_original", sa.String(length=255), nullable=False),
        sa.Column("s3_key", sa.String(length=512), nullable=False),
        sa.Column("mime_type", sa.String(length=100), nullable=False),
        sa.Column("ext", sa.String(length=10), nullable=False),
        sa.Column("size_bytes", sa.Integer(), nullable=False),
        sa.Column("metadata", postgresql.JSONB(astext_type=sa.Text()), server_default=sa.text("'{}'::jsonb"), nullable=False),
    )
    op.create_index("ix_files_owner_id", "files", ["owner_id"])
    op.create_index("ix_files_department_id", "files", ["department_id"])

def downgrade() -> None:
    op.drop_table("files")
    op.drop_index("ix_users_department_id", table_name="users")
    op.drop_index("ix_users_role", table_name="users")
    op.drop_index("ix_users_email", table_name="users")
    op.drop_table("users")
    op.execute("DROP TYPE IF EXISTS userrole")
    op.drop_index("ix_departments_name", table_name="departments")
    op.drop_table("departments")
