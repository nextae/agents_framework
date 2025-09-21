from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.api.dependencies import Credentials
from app.core.auth import encode_access_token, is_valid_user

auth_router = APIRouter(tags=["auth"])


class TokenResponse(BaseModel):
    access_token: str
    token_type: str


@auth_router.post("/login")
async def login(credentials: Credentials) -> TokenResponse:
    """Logs in a user and returns a token response."""

    if not is_valid_user(credentials):
        raise HTTPException(
            status_code=401,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": 'Bearer realm="agents-framework"'},
        )

    access_token = encode_access_token(username=credentials.username)

    return TokenResponse(access_token=access_token, token_type="bearer")
