from pydantic import BaseModel, EmailStr, Field
from typing import Optional

class UserOut(BaseModel):
    id: int
    email: str
    role: str
    department_id: int

class CreateUserRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=6)
    # По умолчанию создаём USER; MANAGER может создавать только USER|MANAGER, ADMIN — любые
    role: Optional[str] = "USER"
    # ADMIN может указать произвольный department_id; MANAGER — игнорируется и берётся свой
    department_id: Optional[int] = None

class UpdateRoleRequest(BaseModel):
    role: str  # "USER" | "MANAGER" | "ADMIN"
