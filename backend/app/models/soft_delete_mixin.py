from __future__ import annotations
from datetime import datetime, timezone
from typing import Optional
from sqlmodel import SQLModel, Field, select
from sqlalchemy.orm import Session

class SoftDeleteMixin(SQLModel):
    deleted_at: Optional[datetime] = Field(
        default=None, index=True, nullable=True
    )
    deleted_by: Optional[str] = Field(default=None, nullable=True)

    @property
    def is_deleted(self) -> bool:
        return self.deleted_at is not None

    def soft_delete(self, by: Optional[str] = None) -> None:
        self.deleted_at = datetime.now(timezone.utc)
        self.deleted_by = by

    def restore(self) -> None:
        self.deleted_at = None
        self.deleted_by = None

    @classmethod
    def alive(cls):
        # convenience for query building
        return cls.deleted_at.is_(None)

    @classmethod
    def dead(cls):
        return cls.deleted_at.is_not(None)
