"""add visibility/status/download_count + unique s3_key

Revision ID: 0002_files_visibility_status
Revises: 0001_init
Create Date: 2025-09-05 00:00:00
"""
from alembic import op
import sqlalchemy as sa

revision = "0002_files_visibility_status"
down_revision = "0001_init"
branch_labels = None
depends_on = None

def upgrade() -> None:
    op.add_column("files", sa.Column("visibility", sa.Enum("PRIVATE","DEPARTMENT","PUBLIC", name="visibility"), nullable=False, server_default="PRIVATE"))
    op.add_column("files", sa.Column("status", sa.Enum("PENDING","READY","FAILED", name="filestatus"), nullable=False, server_default="PENDING"))
    op.add_column("files", sa.Column("download_count", sa.Integer(), nullable=False, server_default="0"))
    # сделать s3_key уникальным, если в 0001 не сделали
    op.create_unique_constraint("uq_files_s3_key", "files", ["s3_key"])

def downgrade() -> None:
    op.drop_constraint("uq_files_s3_key", "files", type_="unique")
    op.drop_column("files", "download_count")
    op.drop_column("files", "status")
    op.drop_column("files", "visibility")
    op.execute("DROP TYPE IF EXISTS visibility")
    op.execute("DROP TYPE IF EXISTS filestatus")
