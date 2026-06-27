import os
from dotenv import load_dotenv
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker, declarative_base

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")
VAULT_DATABASE_URL = os.getenv("VAULT_DATABASE_URL")

if not DATABASE_URL or not VAULT_DATABASE_URL:
    raise ValueError("Database URLs are not set in .env file")

engine = create_async_engine(DATABASE_URL, echo=False)
SessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
Base = declarative_base()

vault_engine = create_async_engine(VAULT_DATABASE_URL, echo=False)
VaultSessionLocal = sessionmaker(
    vault_engine, class_=AsyncSession, expire_on_commit=False
)
VaultBase = declarative_base()


async def get_db():
    async with SessionLocal() as session:
        yield session


async def get_vault_db():
    async with VaultSessionLocal() as session:
        yield session
