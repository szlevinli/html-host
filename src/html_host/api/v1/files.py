from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession

from html_host.api.v1.schemas import ApiResponse, FileResponse
from html_host.core.config import settings
from html_host.core.security import verify_token
from html_host.db.base import get_session
from html_host.services import file_service

router = APIRouter()

_Auth = Annotated[None, Depends(verify_token)]
_Session = Annotated[AsyncSession, Depends(get_session)]


@router.post("", response_model=ApiResponse[FileResponse])
async def upload_file(
    file: UploadFile,
    session: _Session,
    _: _Auth,
) -> ApiResponse[FileResponse]:
    max_bytes = settings.max_file_size_mb * 1024 * 1024
    content = await file.read(max_bytes + 1)
    if len(content) > max_bytes:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"File exceeds {settings.max_file_size_mb} MB",
        )

    record = await file_service.create_file(
        session=session,
        filename=file.filename or "upload.html",
        content=content,
        upload_dir=settings.upload_dir,
    )
    return ApiResponse(
        data=FileResponse(
            short_code=record.short_code,
            filename=record.filename,
            size_bytes=record.size_bytes,
            upload_time=record.upload_time,
            url=f"{settings.base_url}/html/{record.short_code}",
        ),
        error=None,
    )


@router.get("", response_model=ApiResponse[list[FileResponse]])
async def list_files(
    session: _Session,
    _: _Auth,
) -> ApiResponse[list[FileResponse]]:
    files = await file_service.list_files(session)
    return ApiResponse(
        data=[
            FileResponse(
                short_code=f.short_code,
                filename=f.filename,
                size_bytes=f.size_bytes,
                upload_time=f.upload_time,
                url=f"{settings.base_url}/html/{f.short_code}",
            )
            for f in files
        ],
        error=None,
    )


@router.delete("/{code}", response_model=ApiResponse[None])
async def delete_file(
    code: str,
    session: _Session,
    _: _Auth,
) -> ApiResponse[None]:
    deleted = await file_service.delete_file(
        session=session,
        short_code=code,
        upload_dir=settings.upload_dir,
    )
    if not deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)
    return ApiResponse(data=None, error=None)
