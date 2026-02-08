"""SQLAlchemy ORM models."""

from datetime import datetime
from enum import StrEnum

from sqlalchemy import String, Text
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class ContentType(StrEnum):
    """Record content types. Stored as the string value in SQLite."""

    TEXT = "text"
    FILE = "file"


class Base(DeclarativeBase):
    """Declarative base for all ORM models. Required by SQLAlchemy 2.0."""


class Record(Base):
    """Source of truth for all content."""

    __tablename__ = "records"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    content_type: Mapped[str] = mapped_column(
        String(32), default=ContentType.TEXT.value
    )
    source: Mapped[str | None] = mapped_column(String(256), nullable=True)
    created_at: Mapped[datetime] = mapped_column(default=lambda: datetime.now())
