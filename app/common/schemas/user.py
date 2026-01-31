from datetime import datetime
import re
import string
from typing import Optional
from uuid import UUID
from pydantic import BaseModel, Field, field_validator

from app.common.exceptions import BadRequestException


class UserBase(BaseModel):
    name: str = Field("", description="User's name")
    email: str = Field("", description="User's email")
    status: str = Field("", description="User's status")


class UserInfo(UserBase):
    id: UUID = Field(None, description="User's id")
    created_at: datetime = Field(None, description="User's created at")
    updated_at: datetime = Field(None, description="User's updated at")
    image_url: Optional[str] = Field(None, description="User's image url")


class UserCreate(BaseModel):
    name: str = Field(None, description="User's name")
    email: str = Field(None, description="User's email")
    password: str = Field(None, description="User's password")

    @field_validator("password")
    def validate_password(cls, password: str) -> str:
        if len(password) < 8:
            raise BadRequestException("Password must be at least 8 characters long")

        if not any(password_character.isupper() for password_character in password):
            raise BadRequestException(
                "Password must contain at least one uppercase letter"
            )

        if not any(password_character.islower() for password_character in password):
            raise BadRequestException(
                "Password must contain at least one lowercase letter"
            )

        if not any(password_character.isdigit() for password_character in password):
            raise BadRequestException("Password must contain at least one number")

        if not any(
            password_character in string.punctuation for password_character in password
        ):
            raise BadRequestException(
                "Password must contain at least one special character"
            )

        return password

    @field_validator("email")
    def validate_email(cls, email: str) -> str:
        if not re.match(r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$", email):
            raise ValueError("Invalid email address")

        return email


class UserLogin(BaseModel):
    email: str = Field("", description="User's email")
    password: str = Field("", description="User's password")
