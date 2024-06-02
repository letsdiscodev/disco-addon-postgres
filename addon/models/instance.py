from __future__ import annotations

from datetime import datetime, timezone
from secrets import token_hex
from typing import TYPE_CHECKING

from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column, relationship

if TYPE_CHECKING:
    from addon.models import (
        Database,
    )

from addon.models.meta import Base, DateTimeTzAware


class Instance(Base):
    __tablename__ = "instances"

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
    version: Mapped[str] = mapped_column(String(255), nullable=False)
    admin_user: Mapped[str] = mapped_column(String(255), nullable=False)
    admin_password: Mapped[str] = mapped_column(String(255), nullable=False)

    databases: Mapped[list[Database]] = relationship(
        "Database",
        back_populates="instance",
    )

    def log(self):
        return f"INSTANCE_{self.name}"
