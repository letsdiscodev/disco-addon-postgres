from __future__ import annotations

from datetime import datetime, timezone
from secrets import token_hex
from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

if TYPE_CHECKING:
    from addon.models import (
        Attachment,
        Database,
    )

from addon.models.meta import Base, DateTimeTzAware


class User(Base):
    __tablename__ = "users"

    id: Mapped[str] = mapped_column(
        String(32), default=lambda: token_hex(16), primary_key=True
    )
    created: Mapped[datetime] = mapped_column(
        DateTimeTzAware(),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    updated: Mapped[datetime] = mapped_column(
        DateTimeTzAware(),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    password: Mapped[str] = mapped_column(String(255), nullable=False)
    database_id: Mapped[str] = mapped_column(
        String(32),
        ForeignKey("databases.id"),
        nullable=False,
        index=True,
    )

    database: Mapped[Database] = relationship(
        "Database",
        back_populates="users",
    )
    attachments: Mapped[list[Attachment]] = relationship(
        "Attachment",
        back_populates="user",
    )

    def log(self):
        return f"USER_{self.name} ({self.database.name}, {self.database.instance.name})"
