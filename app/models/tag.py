from datetime import datetime
from sqlalchemy import DateTime, String, func
from app.core.database import Base
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.dialects.postgresql import UUID as PostgreSQL_UUID
from uuid import UUID, uuid4


class Tag(Base):
    __tablename__ = "tags"
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

    color: Mapped[str] = mapped_column(String, nullable=False)
    description: Mapped[str] = mapped_column(String, nullable=True)
