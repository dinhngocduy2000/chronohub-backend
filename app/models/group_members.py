from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import DateTime, ForeignKey, PrimaryKeyConstraint, func
from app.common.schemas.group import GroupMemberInfo
from app.core.database import Base
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID as PostgreSQL_UUID


class GroupMembers(Base):
    __tablename__ = "group_members"

    member_id: Mapped[UUID] = mapped_column(
        PostgreSQL_UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        primary_key=True,
        nullable=False,
    )
    group_id: Mapped[UUID] = mapped_column(
        PostgreSQL_UUID(as_uuid=True),
        ForeignKey("groups.id", ondelete="CASCADE"),
        primary_key=True,
        nullable=False,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )

    user: Mapped["User"] = relationship("User", back_populates="groups")  # type: ignore
    group: Mapped["Group"] = relationship("Group", back_populates="members")  # type: ignore

    def view(self) -> GroupMemberInfo:
        return GroupMemberInfo(
            member_id=self.member_id,
            group_id=self.group_id,
            created_at=self.created_at,
            updated_at=self.updated_at,
        )
