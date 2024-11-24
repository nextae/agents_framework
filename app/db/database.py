from collections.abc import AsyncGenerator
from os import getenv

from dotenv import load_dotenv
from sqlalchemy import NullPool
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlmodel.ext.asyncio.session import AsyncSession

load_dotenv()

DATABASE_URL = (
    f"postgresql+asyncpg://"
    f"{getenv('POSTGRES_USER')}:"
    f"{getenv('POSTGRES_PASSWORD')}"
    f"@{getenv('POSTGRES_SERVER')}:5432/{getenv('POSTGRES_DB')}"
)

async_engine = create_async_engine(DATABASE_URL, echo=True, poolclass=NullPool)

Session = async_sessionmaker(async_engine, class_=AsyncSession, expire_on_commit=False)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with Session() as session:
        yield session
