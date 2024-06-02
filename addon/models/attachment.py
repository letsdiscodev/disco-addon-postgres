from __future__ import annotations

from datetime import datetime, timezone
from secrets import token_hex
from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

if TYPE_CHECKING:
    from addon.models import (
        User,
    )

from addon.models.meta import Base, DateTimeTzAware


class Attachment(Base):
    __tablename__ = "attachments"

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
    project_name = mapped_column(String(255), nullable=False)
    env_var = mapped_column(String(255), nullable=False)
    user_id: Mapped[str] = mapped_column(
        String(32),
        ForeignKey("users.id"),
        nullable=False,
        index=True,
    )

    user: Mapped[User] = relationship(
        "User",
        back_populates="attachments",
    )

    def log(self):
        return f"ATTACHMENT_{self.name}"
