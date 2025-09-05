from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.deps import get_db, get_current_user
from app.core.security import create_access_token, verify_password
from app.schemas.auth import LoginRequest, TokenResponse
from app.schemas.user import UserOut
from app.db.models.user import User

router = APIRouter()

@router.post("/login", response_model=TokenResponse)
async def login(data: LoginRequest, db: AsyncSession = Depends(get_db)):
    user = await db.scalar(select(User).where(User.email == data.email))
    if not user or not verify_password(data.password, user.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
    token = create_access_token(sub=str(user.id), data={"role": user.role.value, "dept": user.department_id})
    return TokenResponse(access_token=token)

@router.get("/me", response_model=UserOut)
async def me(current_user: User = Depends(get_current_user)):
    return UserOut(
        id=current_user.id,
        email=current_user.email,
        role=current_user.role.value,
        department_id=current_user.department_id,
    )
