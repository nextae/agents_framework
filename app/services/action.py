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
        return db.get(Action, action_id)

    @staticmethod
    async def create_action(action: Action, db: Session):
        db.add(action)
        db.commit()
        db.refresh(action)
        return action
