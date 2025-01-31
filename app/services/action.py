from sqlalchemy.orm import selectinload
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from app.api.errors import NotFoundError
from app.models.action import (
    Action,
    ActionEvaluationResult,
    ActionRequest,
    ActionUpdateRequest,
)

LOAD_OPTIONS = [selectinload(Action.params)]


class ActionService:
    @staticmethod
    async def create_action(action_request: ActionRequest, db: AsyncSession) -> Action:
        action = Action.model_validate(action_request)

        if action_request.triggered_agent_id is not None:
            from app.services.agent import AgentService

            triggered_agent = await AgentService.get_agent_by_id(
                action_request.triggered_agent_id, db
            )
            if triggered_agent is None:
                raise NotFoundError(
                    f"Agent with id {action_request.triggered_agent_id} not found"
                )

        db.add(action)
        await db.commit()
        await db.refresh(action)
        return action

    @staticmethod
    async def get_actions(db: AsyncSession) -> list[Action]:
        result = await db.exec(select(Action).options(*LOAD_OPTIONS))
        return list(result.all())

    @staticmethod
    async def get_action_by_id(action_id: int, db: AsyncSession) -> Action | None:
        return await db.get(Action, action_id, options=LOAD_OPTIONS)

    @staticmethod
    async def update_action(
        action_id: int, action_update: ActionUpdateRequest, db: AsyncSession
    ) -> Action:
        action = await ActionService.get_action_by_id(action_id, db)
        if not action:
            raise NotFoundError(f"Action with id {action_id} not found")

        action_update_data = action_update.model_dump(exclude_unset=True)

        if action_update.triggered_agent_id is not None:
            from app.services.agent import AgentService

            triggered_agent = await AgentService.get_agent_by_id(
                action_update.triggered_agent_id, db
            )
            if triggered_agent is None:
                raise NotFoundError(
                    f"Agent with id {action_update.triggered_agent_id} not found"
                )

        action.sqlmodel_update(action_update_data)

        db.add(action)
        await db.commit()
        await db.refresh(action)
        return action

    @staticmethod
    async def delete_action(action_id: int, db: AsyncSession) -> None:
        action = await ActionService.get_action_by_id(action_id, db)
        if not action:
            raise NotFoundError(f"Action with id {action_id} not found")

        await db.delete(action)
        await db.commit()

    @staticmethod
    async def agent_has_trigger_actions(agent_id: int, db: AsyncSession) -> bool:
        result = await db.exec(
            select(Action).where(Action.triggered_agent_id == agent_id)
        )
        return result.first() is not None

    @staticmethod
    async def evaluate_action_conditions(
        action_id: int, db: AsyncSession
    ) -> ActionEvaluationResult:
        action = await ActionService.get_action_by_id(action_id, db)
        if action is None:
            raise NotFoundError(f"Action with id {action_id} not found")

        return ActionEvaluationResult(
            action_id=action_id, result=await action.evaluate_conditions(db)
        )
