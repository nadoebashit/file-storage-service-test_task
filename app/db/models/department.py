from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import String
from app.db.base import Base

class Department(Base):
    __tablename__ = "departments"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100), unique=True, index=True)
