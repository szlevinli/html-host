from fastapi import APIRouter

from html_host.api.v1.auth import router as auth_router
from html_host.api.v1.files import router as files_router

router = APIRouter()
router.include_router(auth_router, prefix="/auth", tags=["auth"])
router.include_router(files_router, prefix="/files", tags=["files"])
