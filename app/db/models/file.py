from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy import String, Enum, ForeignKey, Integer
from app.db.base import Base
from app.db.models.enums import Visibility, FileStatus

class File(Base):
    __tablename__ = "files"
    id: Mapped[int] = mapped_column(primary_key=True)
    owner_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    department_id: Mapped[int] = mapped_column(ForeignKey("departments.id"), index=True)

    filename_original: Mapped[str] = mapped_column(String(255))
    s3_key: Mapped[str] = mapped_column(String(512), unique=True)
    mime_type: Mapped[str] = mapped_column(String(100))
    ext: Mapped[str] = mapped_column(String(10))
    size_bytes: Mapped[int] = mapped_column(Integer)

    visibility: Mapped[Visibility] = mapped_column(Enum(Visibility), default=Visibility.PRIVATE, index=True)
    status: Mapped[FileStatus] = mapped_column(Enum(FileStatus), default=FileStatus.PENDING, index=True)
    metadata: Mapped[dict] = mapped_column(JSONB, default={})
    download_count: Mapped[int] = mapped_column(Integer, default=0)

    owner = relationship("User")
