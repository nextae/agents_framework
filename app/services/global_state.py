from sqlmodel import Session

from app.models.global_state import GlobalState

STATE_ID = 1


class GlobalStateService:
    @staticmethod
    async def get_state(db: Session) -> GlobalState:
        state = db.get(GlobalState, STATE_ID)
        assert state is not None
        return state

    @staticmethod
    async def update_state(state: GlobalState, db: Session):
        db.add(state)
        db.commit()
        db.refresh(state)
        return state
