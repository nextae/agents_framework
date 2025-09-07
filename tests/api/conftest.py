import pytest_asyncio

from app.models import Action, ActionConditionOperator
from app.models.action_condition import LogicalOperator


@pytest_asyncio.fixture
async def root_operator(insert) -> ActionConditionOperator:
    action = Action(name="Test Action")
    action = await insert(action)

    root = ActionConditionOperator(logical_operator=LogicalOperator.OR, action_id=action.id)
    root = await insert(root)

    root.root_id = root.id
    return await insert(root)
