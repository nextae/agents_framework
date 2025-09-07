import os
from collections.abc import Generator
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from dotenv import load_dotenv
from socketio import exceptions

from app.core.auth import encode_access_token
from app.sockets.auth import authenticate
from app.sockets.models import AuthPayload

load_dotenv()


@pytest.fixture(scope="module")
def sio() -> Generator[MagicMock, None, None]:
    with patch("app.sockets.auth.sio") as mock_sio:
        mock_sio.emit = AsyncMock()
        yield mock_sio


async def test_authenticate__success(sio, sid):
    # given
    auth_payload = AuthPayload(access_token=encode_access_token(os.getenv("APP_USER")))

    # when, then
    await authenticate(sid, {}, auth_payload.model_dump())


async def test_authenticate__invalid_token(sio, sid):
    # given
    auth_payload = AuthPayload(access_token="invalid")

    # when, then
    with pytest.raises(exceptions.ConnectionRefusedError) as exc_info:
        await authenticate(sid, {}, auth_payload.model_dump())
        assert exc_info.value == "Invalid or expired access token"


@pytest.mark.parametrize("payload", [{}, {"access_token": 123}, {"key": "value"}])
async def test_authenticate__validation_error(sio, sid, payload):
    # when, then
    with pytest.raises(exceptions.ConnectionRefusedError) as exc_info:
        await authenticate(sid, {}, payload)
        assert exc_info.value == "Invalid auth payload"
