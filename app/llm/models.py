from langchain_core.tools import Tool
from pydantic import BaseModel, Field, create_model


# TODO: This is a placeholder model
class ActionArgument(BaseModel):
    name: str
    description: str
    type: type


# TODO: This is a placeholder model
class Action(BaseModel):
    name: str
    description: str
    args: list[ActionArgument]

    def to_tool(self) -> Tool:
        """Converts the action to a LangChain tool."""

        return Tool(
            name=self.name,
            func=lambda: None,  # Just a placeholder as we don't need an actual function
            description=self.description,
            args_schema=self._create_args_schema(),
        )

    def _create_args_schema(self) -> type[BaseModel]:
        """Creates a Pydantic model for the action."""

        return create_model(
            self.name,
            **{
                arg.name: (arg.type, Field(..., description=arg.description))
                for arg in self.args
            },
        )
