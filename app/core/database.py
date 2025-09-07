from os import getenv

from dotenv import load_dotenv
from sqlalchemy import NullPool
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlmodel.ext.asyncio.session import AsyncSession

load_dotenv()

POSTGRES_USER = getenv("POSTGRES_USER")
POSTGRES_PASSWORD = getenv("POSTGRES_PASSWORD")
POSTGRES_SERVER = getenv("POSTGRES_SERVER")
POSTGRES_DB = getenv("POSTGRES_DB")

DATABASE_URL = (
    f"postgresql+asyncpg://{POSTGRES_USER}:{POSTGRES_PASSWORD}@{POSTGRES_SERVER}:5432/{POSTGRES_DB}"
)

async_engine = create_async_engine(DATABASE_URL, poolclass=NullPool)

Session = async_sessionmaker(async_engine, class_=AsyncSession, expire_on_commit=False)
