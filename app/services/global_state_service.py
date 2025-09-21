from app.models.global_state import GlobalState

from .base_service import BaseService

STATE_ID = 1


class GlobalStateService(BaseService):
    async def get_state(self) -> GlobalState:
        """
        Get the global state.

        Returns:
            GlobalState: The global state object.
        """

        async with self.unit_of_work as uow:
            state = await uow.state.find_by_id(STATE_ID)
            if state is None:
                raise ValueError("Global state not found")

            return state

    async def update_state(self, state: GlobalState) -> GlobalState:
        """
        Update the global state.

        Args:
            state (GlobalState): The new global state.

        Returns:
            GlobalState: The updated global state.
        """

        async with self.unit_of_work as uow:
            return await uow.state.update(state)
