from datetime import datetime
from typing import List
from uuid import UUID, uuid4

from sqlalchemy import String, DateTime, func
from app.core.database import Base
from sqlalchemy.dialects.postgresql import UUID as PostgreSQL_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship


class Group(Base):
    __tablename__ = "groups"

    id: Mapped[UUID] = mapped_column(
        PostgreSQL_UUID(as_uuid=True), primary_key=True, default=uuid4, nullable=False
    )
    name: Mapped[str] = mapped_column(String, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )

    members: Mapped[List["GroupMembers"]] = relationship(
        "GroupMembers", back_populates="group"
    )
