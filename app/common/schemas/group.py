from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING, List, Optional
from uuid import UUID
from pydantic import BaseModel, Field

if TYPE_CHECKING:
    from app.common.schemas.user import UserInfo


class GroupInfo(BaseModel):
    id: UUID = Field(None, description="Group's id")
    name: str = Field(None, description="Group's name")
    created_at: datetime = Field(None, description="Group's created at")
    updated_at: datetime = Field(None, description="Group's updated at")
    members: List[UserInfo] = Field(None, description="Group's members")


class GroupCreateDTO(BaseModel):
    name: str = Field(None, description="Group's name")
    description: Optional[str] = Field(None, description="Group's description")
    members: Optional[List[UUID]] = Field(default=[], description="Group's members")


class GroupCreateDomain(GroupCreateDTO):
    owner_id: UUID = Field(None, description="Group's owner id")


class GroupQuery(BaseModel):
    name: Optional[str] = Field(None, description="Group's name")
    id: Optional[UUID] = Field(None, description="Group's id")
    owner_id: Optional[UUID] = Field(None, description="Group's owner id")
