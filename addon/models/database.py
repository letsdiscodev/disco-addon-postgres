from __future__ import annotations

from datetime import datetime, timezone
from secrets import token_hex
from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

if TYPE_CHECKING:
    from addon.models import (
        Instance,
        User,
    )

from addon.models.meta import Base, DateTimeTzAware


class Database(Base):
    __tablename__ = "databases"

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
    instance_id: Mapped[str] = mapped_column(
        String(32),
        ForeignKey("instances.id"),
        nullable=False,
        index=True,
    )

    instance: Mapped[Instance] = relationship(
        "Instance",
        back_populates="databases",
    )
    users: Mapped[list[User]] = relationship(
        "User",
        back_populates="database",
    )

    def log(self):
        return f"DATABASE_{self.name} ({self.instance.name})"
