from pydantic import BaseModel

class UserOut(BaseModel):
    id: int
    email: str
    role: str
    department_id: int
