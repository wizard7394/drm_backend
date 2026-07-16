from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.orm import declarative_base

from app.core.config import settings

if not settings.DATABASE_URL or not settings.VAULT_DATABASE_URL:
    raise ValueError("DATABASE_URL or VAULT_DATABASE_URL is missing in configuration.")

engine = create_async_engine(
    settings.DATABASE_URL,
    echo=False,
    pool_size=20,
    max_overflow=10,
    pool_pre_ping=True,
    pool_recycle=3600,
)

SessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
)
Base = declarative_base()

vault_engine = create_async_engine(
    settings.VAULT_DATABASE_URL,
    echo=False,
    pool_size=20,
    max_overflow=10,
    pool_pre_ping=True,
    pool_recycle=3600,
)

VaultSessionLocal = async_sessionmaker(
    bind=vault_engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
)
VaultBase = declarative_base()


async def get_db():
    async with SessionLocal() as session:
        yield session


async def get_vault_db():
    async with VaultSessionLocal() as session:
        yield session
