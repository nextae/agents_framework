import os
from collections.abc import Generator
from datetime import timedelta
from unittest.mock import patch

import pytest
from dotenv import load_dotenv
from httpx import AsyncClient

from app.api.routes.auth import TokenResponse
from app.core.auth import decode_access_token, encode_access_token

load_dotenv()

pytestmark = pytest.mark.asyncio(loop_scope="session")

ENDPOINTS = [
    # Agents
    ("GET", "/agents"),
    ("GET", "/agents/1"),
    ("POST", "/agents"),
    ("PATCH", "/agents/1"),
    ("DELETE", "/agents/1"),
    ("GET", "/agents/1/messages"),
    ("DELETE", "/agents/1/messages"),
    ("POST", "/agents/assign_action"),
    ("POST", "/agents/remove_action"),
    # Actions
    ("POST", "/actions"),
    ("GET", "/actions"),
    ("GET", "/actions/1"),
    ("PATCH", "/actions/1"),
    ("DELETE", "/actions/1"),
    ("POST", "/actions/1/evaluate_conditions"),
    # Players
    ("GET", "/players"),
    ("GET", "/players/1"),
    ("POST", "/players"),
    ("PATCH", "/players/1"),
    ("DELETE", "/players/1"),
    # Params
    ("POST", "/params"),
    ("GET", "/params/1"),
    ("PATCH", "/params/1"),
    ("DELETE", "/params/1"),
    # Conditions
    ("POST", "/conditions/condition"),
    ("POST", "/conditions/operator"),
    ("POST", "/conditions/tree"),
    ("GET", "/conditions/condition"),
    ("GET", "/conditions/operator"),
    ("GET", "/conditions/condition/1"),
    ("GET", "/conditions/operator/1"),
    ("PATCH", "/conditions/condition/1"),
    ("PATCH", "/conditions/operator/1"),
    ("DELETE", "/conditions/condition/1"),
    ("DELETE", "/conditions/operator/1"),
    ("DELETE", "/conditions/condition_tree/1"),
    ("POST", "/conditions/condition_tree/assign"),
]


@pytest.fixture(scope="module")
def client_no_auth(client: AsyncClient) -> Generator[AsyncClient, None, None]:
    headers = client.headers.copy()
    client.headers = {}
    yield client
    client.headers = headers


@pytest.mark.parametrize("method,path", ENDPOINTS)
async def test_auth__no_token(client_no_auth, method, path):
    # when
    response = await client_no_auth.request(method, path)

    # then
    assert response.status_code == 401


@pytest.mark.parametrize("method,path", ENDPOINTS)
async def test_auth__invalid_token(client_no_auth, method, path):
    # given
    token = "invalid"
    client_no_auth.headers = {"Authorization": f"Bearer {token}"}

    # when
    response = await client_no_auth.request(method, path)

    # then
    assert response.status_code == 401


@pytest.mark.parametrize("method,path", ENDPOINTS)
async def test_auth__expired_token(client_no_auth, method, path):
    # given
    with patch("app.core.auth.JWT_EXPIRES_DELTA", timedelta(seconds=-1)):
        token = encode_access_token(os.getenv("APP_USER"))
    client_no_auth.headers = {"Authorization": f"Bearer {token}"}

    # when
    response = await client_no_auth.request(method, path)

    # then
    assert response.status_code == 401


async def test_login__success(client_no_auth):
    # given
    data = {"username": os.getenv("APP_USER"), "password": os.getenv("APP_PASSWORD")}

    # when
    response = await client_no_auth.post("/login", data=data)

    # then
    assert response.status_code == 200
    token_response = TokenResponse.model_validate(response.json())
    assert token_response.token_type == "bearer"
    assert decode_access_token(token_response.access_token) == os.getenv("APP_USER")


async def test_login__invalid_credentials(client_no_auth):
    # given
    data = {"username": "wrong", "password": "credentials"}

    # when
    response = await client_no_auth.post("/login", data=data)

    # then
    assert response.status_code == 401
    assert response.json()["detail"] == "Incorrect username or password"
    assert response.headers["WWW-Authenticate"] == 'Bearer realm="agents-framework"'
