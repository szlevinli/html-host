import asyncio
import secrets
import string
from datetime import UTC, datetime
from pathlib import Path

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from html_host.db.models import File

_CODE_CHARS = string.ascii_letters + string.digits
_CODE_LENGTH = 8


def _gen_code() -> str:
    return "".join(secrets.choice(_CODE_CHARS) for _ in range(_CODE_LENGTH))


async def create_file(
    session: AsyncSession,
    filename: str,
    content: bytes,
    upload_dir: str,
) -> File:
    for _ in range(5):
        code = _gen_code()
        if await session.scalar(select(File).where(File.short_code == code)) is None:
            break
    else:
        raise RuntimeError("short_code collision after 5 attempts")

    dest = Path(upload_dir) / code
    await asyncio.to_thread(dest.write_bytes, content)

    record = File(
        short_code=code,
        filename=filename,
        size_bytes=len(content),
        upload_time=datetime.now(UTC).isoformat(),
    )
    session.add(record)
    await session.commit()
    await session.refresh(record)
    return record


async def list_files(session: AsyncSession) -> list[File]:
    result = await session.execute(select(File).order_by(File.upload_time.desc()))
    return list(result.scalars().all())


async def delete_file(
    session: AsyncSession,
    short_code: str,
    upload_dir: str,
) -> bool:
    record = await session.scalar(select(File).where(File.short_code == short_code))
    if record is None:
        return False

    dest = Path(upload_dir) / short_code
    await asyncio.to_thread(lambda: dest.unlink(missing_ok=True))

    await session.delete(record)
    await session.commit()
    return True
