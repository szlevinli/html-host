from sqlalchemy import Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from html_host.db.base import Base


class File(Base):
    __tablename__ = "files"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    short_code: Mapped[str] = mapped_column(String, nullable=False, unique=True)
    filename: Mapped[str] = mapped_column(String, nullable=False)
    size_bytes: Mapped[int] = mapped_column(Integer, nullable=False)
    upload_time: Mapped[str] = mapped_column(String, nullable=False)  # ISO 8601
