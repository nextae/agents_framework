from fastapi import APIRouter, Depends
from sqlmodel.ext.asyncio.session import AsyncSession

from app.core.database import get_db
from app.errors.api import NotFoundError
from app.models.player import Player, PlayerRequest, PlayerResponse, PlayerUpdateRequest
from app.services.player import PlayerService

players_router = APIRouter(prefix="/players")


@players_router.get("", response_model=list[PlayerResponse])
async def get_players(db: AsyncSession = Depends(get_db)) -> list[Player]:
    return await PlayerService.get_players(db)


@players_router.get("/{player_id}", response_model=PlayerResponse)
async def get_player(player_id: int, db: AsyncSession = Depends(get_db)) -> Player:
    player = await PlayerService.get_player_by_id(player_id, db)
    if player is None:
        raise NotFoundError(f"Player with id {player_id} not found")

    return player


@players_router.post("", status_code=201, response_model=PlayerResponse)
async def create_player(
    player_create: PlayerRequest, db: AsyncSession = Depends(get_db)
) -> Player:
    return await PlayerService.create_player(player_create, db)


@players_router.put("/{player_id}", response_model=PlayerResponse)
async def update_player(
    player_id: int,
    player_update: PlayerUpdateRequest,
    db: AsyncSession = Depends(get_db),
) -> Player:
    return await PlayerService.update_player(player_id, player_update, db)


@players_router.delete("/{player_id}", status_code=204)
async def delete_player(player_id: int, db: AsyncSession = Depends(get_db)) -> None:
    return await PlayerService.delete_player(player_id, db)
