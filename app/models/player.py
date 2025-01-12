from sqlmodel import Field, SQLModel

from app.llm.models import PlayerDetails


class PlayerBase(SQLModel):
    name: str
    description: str | None = None


class Player(PlayerBase, table=True):
    id: int = Field(default=None, primary_key=True)

    def to_details(self) -> PlayerDetails:
        """Converts the player to player details dict."""

        return PlayerDetails(
            player_id=self.id,
            player_name=self.name,
            player_description=self.description,
        )


class PlayerRequest(PlayerBase):
    pass


class PlayerUpdateRequest(SQLModel):
    name: str | None = None
    description: str | None = None


class PlayerResponse(PlayerBase):
    id: int
