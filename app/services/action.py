from sqlalchemy.orm import selectinload
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from app.models.action import Action
from app.models.action_param import ActionParam


class ActionService:
    @staticmethod
    async def create_action(action: Action, db: AsyncSession) -> Action | None:
        db.add(action)
        await db.commit()
        await db.refresh(action)
        return action

    @staticmethod
    async def create_action_with_params(
        action: Action, params: list[ActionParam], db: AsyncSession
    ) -> tuple[Action | None, list[ActionParam]]:
        db.add(action)
        await db.commit()
        await db.refresh(action)

        for param in params:
            param.action_id = action.id
            db.add(param)

        await db.commit()
        return action, params  # Actually returns [], [].
        # To get the objects I think we'd have to re-select them from db,
        # which is not ideal, but it does add them into the db tho

    @staticmethod
    async def get_actions(db: AsyncSession) -> list[Action]:
        stmt = select(Action)
        result = (await db.exec(stmt)).fetchall()
        return list(result)

    @staticmethod
    async def get_action_by_id(action_id: int, db: AsyncSession) -> Action | None:
        return await db.get(Action, action_id)

    @staticmethod
    async def get_action_with_params(action_id: int, session: AsyncSession):
        stmt = (
            select(Action)
            .options(selectinload(Action.params))
            .where(Action.id == action_id)
        )
        action = (await session.exec(stmt)).first()
        return action

    @staticmethod
    async def update_action(
        action_id: int, updated: Action, db: AsyncSession
    ) -> Action | None:
        stmt = select(Action).where(Action.id == action_id)

        existing_action = (await db.exec(stmt)).first()

        if not existing_action:
            return None

        existing_action.name = updated.name
        existing_action.description = updated.description

        await db.commit()
        await db.refresh(existing_action)

        return existing_action

    @staticmethod
    async def delete_action(action_id: int, db: AsyncSession) -> int | None:
        result = await db.execute(select(Action).filter(Action.id == action_id))
        action = result.scalars().first()

        if not action:
            return None

        await db.delete(action)
        await db.commit()

        return action_id
