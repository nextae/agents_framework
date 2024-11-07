from sqlmodel import Session, select

from app.models.action import Action


class ActionService:
    @staticmethod
    async def get_actions(db: Session) -> list[Action]:
        stmt = select(Action)
        result = db.exec(stmt).fetchall()
        return list(result)

    @staticmethod
    async def get_action(action_id: int, db: Session) -> Action | None:
        stmt = select(Action).where(Action.id == action_id)
        result = db.exec(stmt).fetchall()
        if len(result) == 0:
            return None
        if len(result) == 1:
            return result[0]
        raise Exception(
            f"Found more than one action with id {action_id}. This shouldn't happen"
        )

    @staticmethod
    async def create_action(action: Action, db: Session):
        db.add(action)
        db.commit()
        db.refresh(action)
        return action
