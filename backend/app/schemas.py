import re
from datetime import datetime
from typing import Annotated

from pydantic import AfterValidator, BaseModel, ConfigDict, Field, field_validator

EMAIL_PATTERN = r"^[^@\s]+@[^@\s]+\.[^@\s]+$"
# No "@", so a username can never be mistaken for an email at sign-in.
USERNAME_PATTERN = re.compile(r"[A-Za-z0-9][A-Za-z0-9._-]{2,29}")


def _clean_username(value: str) -> str:
    value = value.strip()
    if not USERNAME_PATTERN.fullmatch(value):
        raise ValueError("A username is 3 to 30 letters, digits, dots, dashes or underscores")
    return value


Username = Annotated[str, AfterValidator(_clean_username)]


class LoginIn(BaseModel):
    login: str = Field(max_length=255)  # email or username
    password: str = Field(max_length=72)  # bcrypt reads at most 72 bytes


class TokenOut(BaseModel):
    access_token: str
    token_type: str = "bearer"


class UserIn(BaseModel):
    email: str = Field(max_length=255, pattern=EMAIL_PATTERN)
    password: str = Field(min_length=8, max_length=72)
    name: str = Field(default="", max_length=80)
    username: Username


class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    username: str
    name: str
    role: str


class ProfileIn(BaseModel):
    name: str = Field(max_length=80)
    username: Username | None = None  # left out: unchanged


class PasswordIn(BaseModel):
    current_password: str = Field(max_length=72)
    new_password: str = Field(min_length=8, max_length=72)


class OwnerOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    username: str
    name: str


class AssignIn(BaseModel):
    user_id: int | None


class ItemIn(BaseModel):
    sku: str = Field(min_length=1, max_length=40)
    name: str = Field(min_length=1, max_length=120)
    quantity: int = Field(default=0, ge=0, le=1_000_000)
    reorder_level: int = Field(default=0, ge=0, le=1_000_000)


class ItemOut(ItemIn):
    model_config = ConfigDict(from_attributes=True)

    id: int
    low_stock: bool
    owner: OwnerOut | None


class MovementIn(BaseModel):
    change: int = Field(ge=-1_000_000, le=1_000_000, description="Positive adds stock, negative removes it.")
    note: str = Field(default="", max_length=200)

    @field_validator("change")
    @classmethod
    def not_zero(cls, value: int) -> int:
        if value == 0:
            raise ValueError("change must not be zero")
        return value


class MovementOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    change: int
    note: str
    user_id: int
    username: str
    created_at: datetime
