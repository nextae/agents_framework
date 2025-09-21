import os
from collections.abc import AsyncGenerator, Generator

import pytest
import pytest_asyncio
import sqlalchemy as sa
from alembic import command as alembic_command
from alembic.config import Config as AlembicConfig
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio.engine import create_async_engine
from testcontainers.postgres import PostgresContainer

from app.core.database import Session
from app.main import socket_app
from app.models import (
    Action,
    ActionCondition,
    ActionConditionOperator,
    ActionParam,
    Agent,
    AgentMessage,
    GlobalState,
    Player,
)
from app.repositories.base_repository import BaseRepository, ModelType
from app.repositories.unit_of_work import UnitOfWork

POSTGRES_USER = os.getenv("POSTGRES_USER")
POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD")
POSTGRES_DB = os.getenv("POSTGRES_DB")
APP_USER = os.getenv("APP_USER")
APP_PASSWORD = os.getenv("APP_PASSWORD")


@pytest.fixture(scope="session", autouse=True)
def setup() -> Generator[PostgresContainer, None, None]:
    """Sets up a Postgres test container, applies migrations, and tears down after tests."""

    alembic_config = AlembicConfig("alembic.ini")

    with PostgresContainer(
        username=POSTGRES_USER, password=POSTGRES_PASSWORD, dbname=POSTGRES_DB, driver="asyncpg"
    ) as postgres:
        connection_url = postgres.get_connection_url()

        alembic_config.set_main_option("sqlalchemy.url", connection_url)
        alembic_command.upgrade(alembic_config, "head", tag="tests")

        engine = create_async_engine(connection_url, poolclass=sa.NullPool)
        Session.configure(bind=engine)

        yield postgres

        alembic_command.downgrade(alembic_config, "base", tag="tests")


@pytest_asyncio.fixture
async def cleanup_db() -> AsyncGenerator[None]:
    yield
    async with Session() as session:
        tables = await session.exec(
            sa.text("SELECT tablename FROM pg_tables WHERE schemaname='public'")
        )
        tables = [table for (table,) in tables.all() if table != "alembic_version"]
        for table in tables:
            await session.exec(sa.text(f"TRUNCATE TABLE {table} CASCADE"))

        global_state = GlobalState(id=1, state={})
        session.add(global_state)
        await session.commit()


@pytest_asyncio.fixture(scope="session")
async def client() -> AsyncGenerator[AsyncClient, None]:
    async with AsyncClient(
        transport=ASGITransport(app=socket_app),
        base_url="http://testserver/api/v1",
        follow_redirects=False,
    ) as client:
        response = await client.post(
            "/login", data={"username": APP_USER, "password": APP_PASSWORD}
        )
        access_token = response.json()["access_token"]
        client.headers["Authorization"] = f"Bearer {access_token}"
        yield client


REPOSITORY_ATTRIBUTES = {
    Action: "actions",
    ActionCondition: "conditions",
    ActionConditionOperator: "operators",
    ActionParam: "params",
    Agent: "agents",
    AgentMessage: "messages",
    GlobalState: "state",
    Player: "players",
}


@pytest.fixture
def insert():
    async def _insert(*models: ModelType) -> list[ModelType] | ModelType:
        async with UnitOfWork() as uow:
            inserted_models = []
            for model in models:
                repository: BaseRepository = getattr(uow, REPOSITORY_ATTRIBUTES[type(model)])
                inserted_models.append(await repository.create(model))

        return inserted_models[0] if len(inserted_models) == 1 else inserted_models

    return _insert
