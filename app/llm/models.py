from pydantic import BaseModel, Field, create_model


# TODO: replace this with a model from the database
class ActionArgument(BaseModel):
    name: str
    description: str
    type: type


# TODO: replace this with a model from the database
class Action(BaseModel):
    name: str
    description: str
    args: list[ActionArgument]

    def to_structured_output(self) -> type[BaseModel]:
        """Converts the action to a structured output model."""

        return create_model(
            self.name,
            **{
                arg.name: (arg.type, Field(..., description=arg.description))
                for arg in self.args
            },
        )
