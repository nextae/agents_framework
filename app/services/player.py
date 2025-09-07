from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from app.errors.api import NotFoundError
from app.models.player import Player, PlayerRequest, PlayerUpdateRequest


class PlayerService:
    @staticmethod
    async def get_players(db: AsyncSession) -> list[Player]:
        result = await db.exec(select(Player))
        return list(result.all())

    @staticmethod
    async def get_player_by_id(player_id: int, db: AsyncSession) -> Player | None:
        return await db.get(Player, player_id)

    @staticmethod
    async def create_player(player_request: PlayerRequest, db: AsyncSession) -> Player:
        player = Player.model_validate(player_request)
        db.add(player)
        await db.commit()
        await db.refresh(player)
        return player

    @staticmethod
    async def update_player(
        player_id: int, player_update: PlayerUpdateRequest, db: AsyncSession
    ) -> Player:
        player = await PlayerService.get_player_by_id(player_id, db)
        if player is None:
            raise NotFoundError(f"Player with id {player_id} not found")

        player_update_data = player_update.model_dump(exclude_unset=True)
        player.sqlmodel_update(player_update_data)

        await db.commit()
        await db.refresh(player)
        return player

    @staticmethod
    async def delete_player(player_id: int, db: AsyncSession) -> None:
        player = await PlayerService.get_player_by_id(player_id, db)
        if player:
            await db.delete(player)
            await db.commit()
