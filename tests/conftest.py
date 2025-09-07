import os
from collections.abc import AsyncGenerator, Callable, Generator
from typing import TypeVar

import pytest
import pytest_asyncio
import sqlalchemy as sa
from alembic import command as alembic_command
from alembic.config import Config as AlembicConfig
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio.engine import create_async_engine
from sqlalchemy.ext.asyncio.session import AsyncSession
from sqlmodel import SQLModel
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
    AgentsActionsMatch,
    GlobalState,
    Player,
)

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


async def _insert_action(session: AsyncSession, action: Action) -> Action:
    session.add(action)
    await session.flush()
    await session.refresh(action)
    return action


async def _insert_action_condition(
    session: AsyncSession, condition: ActionCondition
) -> ActionCondition:
    session.add(condition)
    await session.flush()
    await session.refresh(condition)
    return condition


async def _insert_action_condition_operator(
    session: AsyncSession, condition_operator: ActionConditionOperator
) -> ActionConditionOperator:
    session.add(condition_operator)
    await session.flush()
    await session.refresh(condition_operator)
    return condition_operator


async def _insert_action_param(session: AsyncSession, action_param: ActionParam) -> ActionParam:
    session.add(action_param)
    await session.flush()
    await session.refresh(action_param)
    return action_param


async def _insert_agent(session: AsyncSession, agent: Agent) -> Agent:
    session.add(agent)
    await session.flush()
    await session.refresh(agent)
    return agent


async def _insert_agent_message(session: AsyncSession, agent_message: AgentMessage) -> AgentMessage:
    session.add(agent_message)
    await session.flush()
    await session.refresh(agent_message)
    return agent_message


async def _insert_agents_actions_match(
    session: AsyncSession, match: AgentsActionsMatch
) -> AgentsActionsMatch:
    session.add(match)
    await session.flush()
    await session.refresh(match)
    return match


async def _insert_global_state(session: AsyncSession, state: GlobalState) -> GlobalState:
    state = await session.merge(state)
    await session.flush()
    await session.refresh(state)
    return state


async def _insert_player(session: AsyncSession, player: Player) -> Player:
    session.add(player)
    await session.flush()
    await session.refresh(player)
    return player


ModelType = TypeVar("ModelType", bound=SQLModel)


INSERT_FUNCTIONS: dict[type[SQLModel], Callable] = {
    Action: _insert_action,
    ActionCondition: _insert_action_condition,
    ActionConditionOperator: _insert_action_condition_operator,
    ActionParam: _insert_action_param,
    Agent: _insert_agent,
    AgentMessage: _insert_agent_message,
    AgentsActionsMatch: _insert_agents_actions_match,
    GlobalState: _insert_global_state,
    Player: _insert_player,
}


@pytest.fixture
def insert():
    async def _insert(*models: ModelType) -> list[ModelType] | ModelType:
        async with Session() as session:
            inserted_models = []
            for model in models:
                insert_function = INSERT_FUNCTIONS[type(model)]
                inserted_models.append(await insert_function(session, model))
            await session.commit()
        return inserted_models[0] if len(inserted_models) == 1 else inserted_models

    return _insert
