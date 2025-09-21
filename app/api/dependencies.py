from typing import Annotated

from fastapi import Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm

from app.core.auth import decode_access_token

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/v1/login")
Credentials = Annotated[OAuth2PasswordRequestForm, Depends()]


async def validate_token(token: str = Depends(oauth2_scheme)) -> None:
    if decode_access_token(token) is None:
        raise HTTPException(status_code=401, detail="Invalid token")
