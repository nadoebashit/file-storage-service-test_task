import asyncio
from app.db.session import async_session_maker
from app.db.models.department import Department
from app.db.models.user import User
from app.db.models.enums import UserRole
from app.core.security import hash_password
from sqlalchemy import select

async def seed():
    async with async_session_maker() as s:
        dep = await s.scalar(select(Department).where(Department.name == "IT"))
        if not dep:
            dep = Department(name="IT")
            s.add(dep)
            await s.flush()

        def ensure_user(email: str, pwd: str, role: UserRole):
            return User(email=email, password_hash=hash_password(pwd), role=role, department_id=dep.id)

        existing_admin = await s.scalar(select(User).where(User.email == "admin@example.com"))
        if not existing_admin:
            s.add(ensure_user("admin@example.com", "admin123", UserRole.ADMIN))

        existing_mgr = await s.scalar(select(User).where(User.email == "manager@example.com"))
        if not existing_mgr:
            s.add(ensure_user("manager@example.com", "manager123", UserRole.MANAGER))

        existing_user = await s.scalar(select(User).where(User.email == "user@example.com"))
        if not existing_user:
            s.add(ensure_user("user@example.com", "user123", UserRole.USER))

        await s.commit()
        print("Seed done: admin/manager/user созданы (если отсутствовали)")

if __name__ == "__main__":
    asyncio.run(seed())
