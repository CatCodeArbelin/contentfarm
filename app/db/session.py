import os
from collections.abc import AsyncGenerator, Generator

from sqlalchemy import create_engine
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import Session, sessionmaker


def _database_url() -> str:
    return os.getenv("DATABASE_URL", "sqlite:///./contentfarm.db")


def _async_database_url(database_url: str) -> str:
    if database_url.startswith("postgresql+asyncpg://") or database_url.startswith("sqlite+aiosqlite://"):
        return database_url
    if database_url.startswith("postgresql://"):
        return database_url.replace("postgresql://", "postgresql+asyncpg://", 1)
    if database_url.startswith("sqlite:///"):
        return database_url.replace("sqlite:///", "sqlite+aiosqlite:///", 1)
    return database_url


def _sync_database_url(database_url: str) -> str:
    if database_url.startswith("postgresql+asyncpg://"):
        return database_url.replace("postgresql+asyncpg://", "postgresql://", 1)
    if database_url.startswith("sqlite+aiosqlite://"):
        return database_url.replace("sqlite+aiosqlite://", "sqlite://", 1)
    return database_url


DATABASE_URL = _database_url()
SYNC_DATABASE_URL = _sync_database_url(DATABASE_URL)
ASYNC_DATABASE_URL = os.getenv("ASYNC_DATABASE_URL", _async_database_url(DATABASE_URL))

engine = create_engine(SYNC_DATABASE_URL, pool_pre_ping=True)
async_engine = create_async_engine(ASYNC_DATABASE_URL, pool_pre_ping=True)

SessionLocal = sessionmaker(bind=engine, class_=Session, autoflush=False, autocommit=False, expire_on_commit=False)
AsyncSessionLocal = async_sessionmaker(bind=async_engine, class_=AsyncSession, autoflush=False, expire_on_commit=False)


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


async def get_async_db() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionLocal() as session:
        yield session
