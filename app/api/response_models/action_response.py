from pydantic import BaseModel

from app.models.action import Action
from app.models.action_param import ActionParam


class ActionResponse(BaseModel):
    action: Action
    action_params: list[ActionParam]
