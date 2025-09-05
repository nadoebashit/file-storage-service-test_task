from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import String, ForeignKey, Enum, Boolean
from app.db.base import Base
from app.db.models.enums import UserRole

class User(Base):
    __tablename__ = "users"
    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String(255))
    role: Mapped[UserRole] = mapped_column(Enum(UserRole), default=UserRole.USER, index=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    department_id: Mapped[int] = mapped_column(ForeignKey("departments.id"), index=True)
    department = relationship("Department")
