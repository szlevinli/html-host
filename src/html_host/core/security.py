from datetime import datetime, timedelta, timezone
from typing import Annotated

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from html_host.core.config import settings

_bearer = HTTPBearer()
_ALGORITHM = "HS256"


def create_access_token() -> str:
    expire = datetime.now(timezone.utc) + timedelta(days=settings.jwt_expire_days)
    return jwt.encode({"exp": expire}, settings.jwt_secret, algorithm=_ALGORITHM)


def verify_token(
    credentials: Annotated[HTTPAuthorizationCredentials, Depends(_bearer)],
) -> None:
    try:
        jwt.decode(
            credentials.credentials,
            settings.jwt_secret,
            algorithms=[_ALGORITHM],
        )
    except jwt.PyJWTError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED)
