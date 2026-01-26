from datetime import datetime
from typing import List
from uuid import UUID, uuid4

from sqlalchemy import Enum, String, DateTime, func
from sqlalchemy.dialects.postgresql import UUID as PostgreSQL_UUID
from app.common.enum.user_status import UserStatus
from app.common.schemas.user import UserInfo
from app.core.database import Base
from sqlalchemy.orm import (
    Mapped,
    mapped_column,
    relationship,
)


class User(Base):
    __tablename__ = "users"

    id: Mapped[UUID] = mapped_column(
        PostgreSQL_UUID(as_uuid=True), primary_key=True, default=uuid4, nullable=False
    )
    name: Mapped[str] = mapped_column(String(50), nullable=False)
    email: Mapped[str] = mapped_column(String(50), nullable=False, unique=True)
    status: Mapped[UserStatus] = mapped_column(
        Enum(UserStatus), nullable=False, default=UserStatus.PENDING, index=True
    )
    password: Mapped[str] = mapped_column(String(16), nullable=True)
    image_url: Mapped[str] = mapped_column(String(255), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )

    groups: Mapped[List["GroupMembers"]] = relationship(  # type: ignore
        "GroupMembers", back_populates="user"
    )

    owned_groups: Mapped[List["Group"]] = relationship(  # type: ignore
        "Group", back_populates="owner"
    )

    def view(self) -> UserInfo:
        return UserInfo(
            id=self.id,
            name=self.name,
            email=self.email,
            status=self.status,
            created_at=self.created_at,
            updated_at=self.updated_at,
            image_url=self.image_url,
        )
