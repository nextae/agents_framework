from app.core.database import Session

from .action_condition_operator_repository import ActionConditionOperatorRepository
from .action_condition_repository import ActionConditionRepository
from .action_param_repository import ActionParamRepository
from .action_repository import ActionRepository
from .agent_message_repository import AgentMessageRepository
from .agent_repository import AgentRepository
from .global_state_repository import GlobalStateRepository
from .player_repository import PlayerRepository


class UnitOfWork:
    actions: ActionRepository
    agents: AgentRepository
    conditions: ActionConditionRepository
    messages: AgentMessageRepository
    operators: ActionConditionOperatorRepository
    params: ActionParamRepository
    players: PlayerRepository
    state: GlobalStateRepository

    def __init__(self) -> None:
        self._depth = 0

    async def __aenter__(self) -> "UnitOfWork":
        """
        Creates a database session and initializes repositories.
        Nested usages of the unit of work will share the same session.

        Returns:
            UnitOfWork: The unit of work instance.
        """

        self._depth += 1
        if self._depth > 1:
            return self

        self._session = await Session().__aenter__()

        self.actions = ActionRepository(self._session)
        self.agents = AgentRepository(self._session)
        self.conditions = ActionConditionRepository(self._session)
        self.messages = AgentMessageRepository(self._session)
        self.operators = ActionConditionOperatorRepository(self._session)
        self.params = ActionParamRepository(self._session)
        self.players = PlayerRepository(self._session)
        self.state = GlobalStateRepository(self._session)

        return self

    async def __aexit__(
        self,
        exc_type: type | None,
        exc_val: BaseException | None,
        exc_tb: object | None,
    ) -> None:
        self._depth = max(self._depth - 1, 0)
        if self._depth > 0:
            return

        if exc_val:
            await self.rollback()
        else:
            await self.commit()

        await self._session.__aexit__(exc_type, exc_val, exc_tb)

    async def commit(self) -> None:
        await self._session.commit()

    async def rollback(self) -> None:
        await self._session.rollback()
