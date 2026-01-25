from datetime import datetime
from typing import List
from uuid import UUID
from pydantic import BaseModel, Field

from app.common.schemas.user import UserInfo


class GroupInfo(BaseModel):
    id: UUID = Field(None, description="Group's id")
    name: str = Field(None, description="Group's name")
    created_at: datetime = Field(None, description="Group's created at")
    updated_at: datetime = Field(None, description="Group's updated at")
    members: List[UserInfo] = Field(None, description="Group's members")
