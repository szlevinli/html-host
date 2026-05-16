from datetime import datetime

from pydantic import BaseModel


class FileResponse(BaseModel):
    short_code: str
    filename: str
    size_bytes: int
    upload_time: datetime
    url: str


class ErrorDetail(BaseModel):
    code: str
    message: str


class ApiResponse[T](BaseModel):
    data: T | None
    error: ErrorDetail | None
