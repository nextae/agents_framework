import pytest

from app.core.database import Session
from app.models.player import Player, PlayerRequest, PlayerResponse, PlayerUpdateRequest
from app.services.player import PlayerService


async def test_get_players__success(client, insert, cleanup_db):
    # given
    players = [
        Player(name="Player 1", description="desc 1"),
        Player(name="Player 2", description="desc 2"),
    ]
    players = await insert(*players)

    # when
    response = await client.get("/players")

    # then
    assert response.status_code == 200
    assert [Player.model_validate(p) for p in response.json()] == players


async def test_create_player__success(client, cleanup_db):
    # given
    request = PlayerRequest(name="Test Player", description="desc")

    # when
    response = await client.post("/players", json=request.model_dump())

    # then
    assert response.status_code == 201
    response_player = PlayerResponse.model_validate(response.json())
    assert response_player.name == request.name
    assert response_player.description == request.description


@pytest.mark.parametrize(
    "payload", [{}, {"name": 999}, {"description": "desc"}, {"name": "name", "description": 999}]
)
async def test_create_player__unprocessable_entity(client, payload):
    # when
    response = await client.post("/players", json=payload)

    # then
    assert response.status_code == 422


async def test_get_player_by_id__success(client, insert, cleanup_db):
    # given
    player = Player(name="Player", description="desc")
    player = await insert(player)

    # when
    response = await client.get(f"/players/{player.id}")

    # then
    assert response.status_code == 200
    assert Player.model_validate(response.json()) == player


async def test_get_player_by_id__not_found(client, cleanup_db):
    # given
    player_id = 999

    # when
    response = await client.get(f"/players/{player_id}")

    # then
    assert response.status_code == 404
    assert f"Player with id {player_id} not found" in response.text


async def test_get_player_by_id__unprocessable_entity(client):
    # given
    player_id = "invalid"

    # when
    response = await client.get(f"/players/{player_id}")

    # then
    assert response.status_code == 422


async def test_update_player__success(client, insert, cleanup_db):
    # given
    player = Player(name="Old Name", description="Old Desc")
    player = await insert(player)
    request = PlayerUpdateRequest(name="New Name", description="New Desc")

    # when
    response = await client.patch(f"/players/{player.id}", json=request.model_dump())

    # then
    assert response.status_code == 200
    updated_player = Player.model_validate(response.json())
    assert updated_player.name == request.name
    assert updated_player.description == request.description


async def test_update_player__not_found(client, cleanup_db):
    # given
    player_id = 999
    request = PlayerUpdateRequest(name="New Name")

    # when
    response = await client.patch(f"/players/{player_id}", json=request.model_dump())

    # then
    assert response.status_code == 404
    assert f"Player with id {player_id} not found" in response.text


async def test_update_player__unprocessable_entity(client, insert, cleanup_db):
    # given
    player = Player(name="Player")
    player = await insert(player)
    request = {"name": 999}

    # when
    response = await client.patch(f"/players/{player.id}", json=request)

    # then
    assert response.status_code == 422


async def test_delete_player__success(client, insert, cleanup_db):
    # given
    player = Player(name="Player to Delete")
    player = await insert(player)

    # when
    response = await client.delete(f"/players/{player.id}")

    # then
    assert response.status_code == 204
    async with Session() as db:
        assert await PlayerService.get_player_by_id(player.id, db) is None


async def test_delete_player__not_found(client, cleanup_db):
    # given
    player_id = 999

    # when
    response = await client.delete(f"/players/{player_id}")

    # then
    assert response.status_code == 204
