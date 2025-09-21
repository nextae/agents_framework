from abc import ABC
from typing import TypeVar

from sqlalchemy.exc import IntegrityError
from sqlmodel import SQLModel, select
from sqlmodel.ext.asyncio.session import AsyncSession

__all__ = ("BaseRepository", "ModelType")


ModelType = TypeVar("ModelType", bound=SQLModel)


class BaseRepository[ModelType](ABC):
    _session: AsyncSession
    _model_cls: type[ModelType]

    def __init__(self, session: AsyncSession, model_cls: type[ModelType]) -> None:
        self._session = session
        self._model_cls = model_cls

    async def find_by_id(self, id_: int) -> ModelType | None:
        return await self._session.get(self._model_cls, id_)

    async def find_all(self) -> list[ModelType]:
        result = await self._session.exec(select(self._model_cls))
        return list(result.all())

    async def find_all_by_ids(self, ids: list[int]) -> list[ModelType]:
        if not ids:
            return []

        result = await self._session.exec(
            select(self._model_cls).where(self._model_cls.id.in_(ids))
        )
        return list(result.all())

    async def create(self, model: ModelType) -> ModelType:
        try:
            self._session.add(model)
            await self._session.flush()
            await self._session.refresh(model)
            return model
        except IntegrityError:
            await self._session.rollback()
            raise

    async def update(self, model: ModelType) -> ModelType:
        try:
            self._session.add(model)
            await self._session.flush()
            await self._session.refresh(model)
            return model
        except IntegrityError:
            await self._session.rollback()
            raise

    async def delete(self, model: ModelType) -> None:
        await self._session.delete(model)

    async def delete_by_id(self, model_id: int) -> None:
        model = await self.find_by_id(model_id)
        if model:
            await self._session.delete(model)
