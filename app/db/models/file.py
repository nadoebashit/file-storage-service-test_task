from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy import String, Enum, ForeignKey, Integer
from app.db.base import Base

# На День 1 без enum Visibility/FileStatus — добавим в День 2
class File(Base):
    __tablename__ = "files"
    id: Mapped[int] = mapped_column(primary_key=True)
    owner_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    department_id: Mapped[int] = mapped_column(ForeignKey("departments.id"), index=True)

    filename_original: Mapped[str] = mapped_column(String(255))
    s3_key: Mapped[str] = mapped_column(String(512))
    mime_type: Mapped[str] = mapped_column(String(100))
    ext: Mapped[str] = mapped_column(String(10))
    size_bytes: Mapped[int] = mapped_column(Integer)
    metadata: Mapped[dict] = mapped_column(JSONB, default={})

    owner = relationship("User")
