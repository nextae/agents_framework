from sqlmodel.ext.asyncio.session import AsyncSession

from app.models.global_state import GlobalState

STATE_ID = 1


class GlobalStateService:
    @staticmethod
    async def get_state(db: AsyncSession) -> GlobalState:
        state = await db.get(GlobalState, STATE_ID)
        assert state is not None
        return state

    @staticmethod
    async def update_state(state: GlobalState, db: AsyncSession):
        db.add(state)
        await db.commit()
        await db.refresh(state)
        return state
