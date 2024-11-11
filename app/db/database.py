from collections.abc import AsyncGenerator
from os import getenv

from dotenv import load_dotenv
from sqlalchemy.ext.asyncio import create_async_engine
from sqlmodel.ext.asyncio.session import AsyncSession

load_dotenv()

DATABASE_URL = (
    f"postgresql+asyncpg://"
    f"{getenv('POSTGRES_USER')}:"
    f"{getenv('POSTGRES_PASSWORD')}"
    f"@{getenv('POSTGRES_SERVER')}:5432/{getenv('POSTGRES_DB')}"
)

async_engine = create_async_engine(DATABASE_URL, echo=True)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    db = AsyncSession(async_engine)
    try:
        yield db
    finally:
        await db.close()
