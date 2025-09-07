from alembic import op
import sqlalchemy as sa

revision = "0002_files_visibility_status"
down_revision = "0001_init"
branch_labels = None
depends_on = None

def upgrade() -> None:
    bind = op.get_bind()

    # Явно создаём enum-типы в БД (идемпотентно)
    visibility_enum = sa.Enum("PRIVATE", "DEPARTMENT", "PUBLIC", name="visibility")
    status_enum = sa.Enum("PENDING", "READY", "FAILED", name="filestatus")
    visibility_enum.create(bind, checkfirst=True)
    status_enum.create(bind, checkfirst=True)

    # Затем добавляем колонки
    op.add_column(
        "files",
        sa.Column(
            "visibility",
            visibility_enum,
            nullable=False,
            server_default=sa.text("'PRIVATE'"),
        ),
    )
    op.add_column(
        "files",
        sa.Column(
            "status",
            status_enum,
            nullable=False,
            server_default=sa.text("'PENDING'"),
        ),
    )
    op.add_column(
        "files",
        sa.Column("download_count", sa.Integer(), nullable=False, server_default="0"),
    )

    # Уникальность ключа в S3 (если ещё не было)
    op.create_unique_constraint("uq_files_s3_key", "files", ["s3_key"])

    # (опционально) убрать server_default, чтобы значение не прилипло навсегда
    op.alter_column("files", "visibility", server_default=None)
    op.alter_column("files", "status", server_default=None)


def downgrade() -> None:
    # Сначала убираем зависимости от типов
    op.drop_constraint("uq_files_s3_key", "files", type_="unique")
    op.drop_column("files", "download_count")
    op.drop_column("files", "status")
    op.drop_column("files", "visibility")

    bind = op.get_bind()
    # Потом удаляем типы
    sa.Enum(name="filestatus").drop(bind, checkfirst=True)
    sa.Enum(name="visibility").drop(bind, checkfirst=True)
