from app.errors.api import NotFoundError
from app.models.player import Player, PlayerRequest, PlayerUpdateRequest
from app.services.base_service import BaseService


class PlayerService(BaseService):
    async def get_players(self) -> list[Player]:
        """
        Get all players.

        Returns:
            list[Player]: A list of all players.
        """

        async with self.unit_of_work as uow:
            return await uow.players.find_all()

    async def get_player_by_id(self, player_id: int) -> Player | None:
        """
        Get a player by its ID.

        Args:
            player_id (int): The ID of the player to retrieve.

        Returns:
            Player | None: The player with the specified ID, or None if not found.
        """

        async with self.unit_of_work as uow:
            return await uow.players.find_by_id(player_id)

    async def create_player(self, player_request: PlayerRequest) -> Player:
        """
        Create a new player.

        Args:
            player_request (PlayerRequest): The request to create the new player.

        Returns:
            Player: The created player.
        """

        player = Player.model_validate(player_request)

        async with self.unit_of_work as uow:
            return await uow.players.create(player)

    async def update_player(self, player_id: int, player_update: PlayerUpdateRequest) -> Player:
        """
        Update an existing player.

        Args:
            player_id (int): The ID of the player to update.
            player_update (PlayerUpdateRequest): The request to update the player.

        Returns:
            Player: The updated player.
        """

        async with self.unit_of_work as uow:
            player = await self.get_player_by_id(player_id)
            if player is None:
                raise NotFoundError(f"Player with id {player_id} not found")

            player_update_data = player_update.model_dump(exclude_unset=True)
            player.sqlmodel_update(player_update_data)

            return await uow.players.update(player)

    async def delete_player(self, player_id: int) -> None:
        """
        Delete a player by its ID.

        Args:
            player_id (int): The ID of the player to delete.
        """

        async with self.unit_of_work as uow:
            await uow.players.delete_by_id(player_id)
