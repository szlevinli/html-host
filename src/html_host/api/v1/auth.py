from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel

from html_host.core.config import settings
from html_host.core.security import create_access_token

router = APIRouter()


class LoginRequest(BaseModel):
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


@router.post("/login", response_model=TokenResponse)
async def login(body: LoginRequest) -> TokenResponse:
    if body.password != settings.admin_password:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED)
    return TokenResponse(access_token=create_access_token())
