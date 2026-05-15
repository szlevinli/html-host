import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from html_host.services import file_service


@pytest.mark.asyncio
async def test_create_file(db_session: AsyncSession, tmp_path: pytest.TempPathFactory) -> None:
    upload_dir = str(tmp_path)
    record = await file_service.create_file(
        session=db_session,
        filename="test.html",
        content=b"<p>test</p>",
        upload_dir=upload_dir,
    )
    assert len(record.short_code) == 8
    assert record.size_bytes == 11
    assert record.filename == "test.html"


@pytest.mark.asyncio
async def test_short_code_uniqueness(db_session: AsyncSession, tmp_path: pytest.TempPathFactory) -> None:
    upload_dir = str(tmp_path)
    records = [
        await file_service.create_file(
            session=db_session,
            filename=f"f{i}.html",
            content=b"x",
            upload_dir=upload_dir,
        )
        for i in range(10)
    ]
    codes = {r.short_code for r in records}
    assert len(codes) == 10


@pytest.mark.asyncio
async def test_delete_nonexistent(db_session: AsyncSession, tmp_path: pytest.TempPathFactory) -> None:
    result = await file_service.delete_file(
        session=db_session,
        short_code="notexist",
        upload_dir=str(tmp_path),
    )
    assert result is False
