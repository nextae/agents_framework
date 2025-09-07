import logging
from typing import Any

import pydantic
from socketio import exceptions

from app.core.auth import decode_access_token

from .models import AuthPayload
from .server import sio

logger = logging.getLogger(__name__)


@sio.on("connect")
async def authenticate(sid: str, _environ: dict[str, Any], auth: dict[str, str]) -> None:
    """Handles connection and authentication of a client."""

    try:
        auth_payload = AuthPayload.model_validate(auth)
    except pydantic.ValidationError:
        logger.info(f"Socket client {sid} provided invalid auth payload")
        raise exceptions.ConnectionRefusedError("Invalid auth payload")

    if decode_access_token(auth_payload.access_token) is None:
        logger.info(f"Socket client {sid} provided invalid or expired access token")
        raise exceptions.ConnectionRefusedError("Invalid or expired access token")

    logger.info(f"Socket client connected: {sid}")
