from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional

from app.core.deps import get_db, get_current_user, require_manager_or_admin, require_admin
from app.core.security import hash_password
from app.db.models.user import User
from app.db.models.department import Department
from app.db.models.enums import UserRole
from app.schemas.user import UserOut, CreateUserRequest, UpdateRoleRequest

router = APIRouter()

def _user_to_out(u: User) -> UserOut:
    return UserOut(
        id=u.id,
        email=u.email,
        role=u.role.value,
        department_id=u.department_id,
    )

@router.post("/", response_model=UserOut, summary="Создание пользователя (MANAGER/ADMIN)")
async def create_user(
    data: CreateUserRequest,
    db: AsyncSession = Depends(get_db),
    me: User = Depends(require_manager_or_admin),
):
    # Проверка уникальности email
    existing = await db.scalar(select(User).where(User.email == data.email))
    if existing:
        raise HTTPException(status_code=400, detail="Email already exists")

    # Определяем департамент и допустимую роль
    if me.role == UserRole.ADMIN:
        department_id = data.department_id or me.department_id
        # Проверка что департамент существует
        dep = await db.scalar(select(Department).where(Department.id == department_id))
        if not dep:
            raise HTTPException(status_code=400, detail="Department not found")
        # ADMIN может любую роль
        role_str = (data.role or "USER").upper()
        try:
            role = UserRole(role_str)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid role")
    else:
        # MANAGER: создаёт только в СВОЙ департамент
        department_id = me.department_id
        role_str = (data.role or "USER").upper()
        if role_str not in ("USER", "MANAGER"):
            raise HTTPException(status_code=403, detail="Manager cannot assign ADMIN role")
        role = UserRole(role_str)

    u = User(
        email=data.email,
        password_hash=hash_password(data.password),
        role=role,
        department_id=department_id,
    )
    db.add(u)
    await db.commit()
    await db.refresh(u)
    return _user_to_out(u)

@router.get("/{user_id}", response_model=UserOut, summary="Информация о пользователе (MANAGER/ADMIN)")
async def get_user(
    user_id: int,
    db: AsyncSession = Depends(get_db),
    me: User = Depends(require_manager_or_admin),
):
    u = await db.scalar(select(User).where(User.id == user_id))
    if not u:
        raise HTTPException(status_code=404, detail="User not found")

    # MANAGER видит только свой департамент
    if me.role == UserRole.MANAGER and u.department_id != me.department_id:
        raise HTTPException(status_code=403, detail="Forbidden: other department")

    return _user_to_out(u)

@router.put("/{user_id}/role", response_model=UserOut, summary="Изменение роли пользователя (MANAGER/ADMIN)")
async def change_role(
    user_id: int,
    payload: UpdateRoleRequest,
    db: AsyncSession = Depends(get_db),
    me: User = Depends(require_manager_or_admin),
):
    u = await db.scalar(select(User).where(User.id == user_id))
    if not u:
        raise HTTPException(status_code=404, detail="User not found")

    new_role_str = payload.role.upper()
    # Валидация роли
    try:
        new_role = UserRole(new_role_str)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid role")

    # Ограничения:
    # - ADMIN может менять любую роль
    # - MANAGER может менять только пользователей своего департамента
    #   и не может повысить кого-то до ADMIN и трогать существующих ADMIN
    if me.role == UserRole.MANAGER:
        if u.department_id != me.department_id:
            raise HTTPException(status_code=403, detail="Forbidden: other department")
        if new_role == UserRole.ADMIN:
            raise HTTPException(status_code=403, detail="Manager cannot assign ADMIN role")
        if u.role == UserRole.ADMIN:
            raise HTTPException(status_code=403, detail="Manager cannot modify ADMIN user")

    await db.execute(
        update(User).where(User.id == user_id).values(role=new_role)
    )
    await db.commit()
    # вернуть обновлённого
    u = await db.scalar(select(User).where(User.id == user_id))
    return _user_to_out(u)

@router.get("/", response_model=List[UserOut], summary="Список пользователей отдела (MANAGER/ADMIN)")
async def list_users(
    db: AsyncSession = Depends(get_db),
    me: User = Depends(require_manager_or_admin),
    department_id: Optional[int] = Query(None, description="Фильтр по отделу (ADMIN может любой, MANAGER — только свой)"),
):
    q = select(User)
    if me.role == UserRole.ADMIN:
        if department_id:
            q = q.where(User.department_id == department_id)
    else:
        # MANAGER — всегда только свой департамент, игнорируем чужие
        q = q.where(User.department_id == me.department_id)

    users = (await db.scalars(q.order_by(User.id))).all()
    return [_user_to_out(u) for u in users]
