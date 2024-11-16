from sqlalchemy.orm import selectinload
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from app.models.action import Action
from app.models.action_param import ActionParam
from app.models.agents_actions_matches import AgentsActionsMatches


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
    ) -> Action:
        db.add(action)
        await db.commit()
        await db.refresh(action)

        for param in params:
            param.action_id = action.id
            db.add(param)

        await db.commit()
        return action

    @staticmethod
    async def get_actions(db: AsyncSession) -> list[Action]:
        stmt = select(Action).options(selectinload(Action.params))
        result = (await db.exec(stmt)).fetchall()
        return list(result)

    @staticmethod
    async def get_action_by_id(action_id: int, db: AsyncSession) -> Action:
        stmt = (
            select(Action)
            .options(selectinload(Action.params))
            .where(Action.id == action_id)
        )
        action = (await db.exec(stmt)).first()
        return action

    @staticmethod
    async def update_action(
        action_id: int, updated: Action, db: AsyncSession
    ) -> Action | None:
        existing_action = await ActionService.get_action_by_id(action_id, db)

        if not existing_action:
            raise ValueError(f"Action with id={action_id} not found")

        existing_action.name = updated.name
        existing_action.description = updated.description

        await db.commit()
        await db.refresh(existing_action)

        return existing_action

    @staticmethod
    async def delete_action(action_id: int, db: AsyncSession) -> int | None:
        action = await ActionService.get_action_by_id(action_id, db)

        if not action:
            raise ValueError(f"Action with id={action_id} not found")

        matches = await db.exec(
            select(AgentsActionsMatches).where(
                AgentsActionsMatches.action_id == action_id
            )
        )

        for match in matches:
            await db.delete(match)

        params = await db.exec(
            select(ActionParam).where(ActionParam.action_id == action_id)
        )
        for param in params:
            await db.delete(param)

        await db.delete(action)
        await db.commit()

        return action_id
