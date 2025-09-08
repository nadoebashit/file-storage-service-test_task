# app/db/session.py
from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from app.core.config import settings

engine = create_async_engine(settings.DATABASE_URL, pool_pre_ping=True, future=True, echo=False)

# <-- это то, что импортирует Celery-задача
async_session_maker = async_sessionmaker(bind=engine, expire_on_commit=False, class_=AsyncSession)

# совместимость (если где-то используешь старое имя)
AsyncSessionLocal = async_session_maker

async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with async_session_maker() as session:
        yield session
