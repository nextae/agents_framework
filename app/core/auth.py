import os
from datetime import UTC, datetime, timedelta
from typing import Any

import jwt
from dotenv import load_dotenv
from fastapi.security import OAuth2PasswordRequestForm

__all__ = (
    "encode_access_token",
    "decode_access_token",
    "is_valid_user",
)

load_dotenv()

JWT_ALGORITHM = "HS256"
JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY")
JWT_EXPIRES_DELTA = timedelta(hours=8)

USERNAME = os.getenv("APP_USER")
PASSWORD = os.getenv("APP_PASSWORD")


def is_valid_user(credentials: OAuth2PasswordRequestForm) -> bool:
    """Checks if the credentials are valid."""

    return credentials.username == USERNAME and credentials.password == PASSWORD


def encode_access_token(username: str) -> str:
    """Encodes the JWT token for the given username."""

    data = {"sub": username, "exp": datetime.now(UTC) + JWT_EXPIRES_DELTA}
    return jwt.encode(data, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)


def decode_access_token(access_token: str) -> str | None:
    """
    Decodes the JWT token and returns the username or None if the token is invalid.
    """

    try:
        payload: dict[str, Any] = jwt.decode(
            access_token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM]
        )
        return payload["sub"]
    except jwt.PyJWTError:
        return None
