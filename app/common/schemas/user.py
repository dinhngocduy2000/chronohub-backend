from datetime import datetime
from uuid import UUID
from pydantic import BaseModel, Field


class UserBase(BaseModel):
    name: str = Field("", description="User's name")
    email: str = Field("", description="User's email")
    status: str = Field("", description="User's status")


class UserInfo(UserBase):
    id: UUID = Field(None, description="User's id")
    created_at: datetime = Field(None, description="User's created at")
    updated_at: datetime = Field(None, description="User's updated at")
    image_url: str = Field(None, description="User's image url")
