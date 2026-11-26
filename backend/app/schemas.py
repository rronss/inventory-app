from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator

EMAIL_PATTERN = r"^[^@\s]+@[^@\s]+\.[^@\s]+$"


class LoginIn(BaseModel):
    email: str = Field(max_length=255)
    password: str = Field(max_length=72)  # bcrypt reads at most 72 bytes


class TokenOut(BaseModel):
    access_token: str
    token_type: str = "bearer"


class UserIn(BaseModel):
    email: str = Field(max_length=255, pattern=EMAIL_PATTERN)
    password: str = Field(min_length=8, max_length=72)


class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    email: str
    role: str


class ItemIn(BaseModel):
    sku: str = Field(min_length=1, max_length=40)
    name: str = Field(min_length=1, max_length=120)
    quantity: int = Field(default=0, ge=0, le=1_000_000)
    reorder_level: int = Field(default=0, ge=0, le=1_000_000)


class ItemOut(ItemIn):
    model_config = ConfigDict(from_attributes=True)

    id: int
    low_stock: bool


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
    created_at: datetime
