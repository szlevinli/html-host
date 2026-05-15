from typing import Generic, TypeVar

from pydantic import BaseModel

T = TypeVar("T")


class FileResponse(BaseModel):
    short_code: str
    filename: str
    size_bytes: int
    upload_time: str
    url: str


class ErrorDetail(BaseModel):
    code: str
    message: str


class ApiResponse(BaseModel, Generic[T]):
    data: T | None
    error: ErrorDetail | None
