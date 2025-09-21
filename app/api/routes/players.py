from fastapi import APIRouter, Depends

from app.api.dependencies import validate_token
from app.errors.api import NotFoundError
from app.models.player import Player, PlayerRequest, PlayerResponse, PlayerUpdateRequest
from app.services.player_service import PlayerService

players_router = APIRouter(
    prefix="/players", tags=["players"], dependencies=[Depends(validate_token)]
)


@players_router.get("", response_model=list[PlayerResponse])
async def get_players() -> list[Player]:
    return await PlayerService().get_players()


@players_router.get("/{player_id}", response_model=PlayerResponse)
async def get_player(player_id: int) -> Player:
    player = await PlayerService().get_player_by_id(player_id)
    if player is None:
        raise NotFoundError(f"Player with id {player_id} not found")

    return player


@players_router.post("", status_code=201, response_model=PlayerResponse)
async def create_player(player_create: PlayerRequest) -> Player:
    return await PlayerService().create_player(player_create)


@players_router.patch("/{player_id}", response_model=PlayerResponse)
async def update_player(player_id: int, player_update: PlayerUpdateRequest) -> Player:
    return await PlayerService().update_player(player_id, player_update)


@players_router.delete("/{player_id}", status_code=204)
async def delete_player(player_id: int) -> None:
    await PlayerService().delete_player(player_id)
