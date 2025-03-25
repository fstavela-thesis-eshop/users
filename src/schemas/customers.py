from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field


class AuthResponse(BaseModel):
    customer_id: UUID = Field(alias="id")

class CustomerBase(BaseModel):
    username: str
    first_name: str
    last_name: str
    email: EmailStr
    address: str
    phone: str

    class Config:
        extra = "forbid"


class CustomerCreate(CustomerBase):
    password: str


class CustomerUpdate(BaseModel):
    username: str | None = None
    password: str | None = None
    first_name: str | None = None
    last_name: str | None = None
    email: EmailStr | None = None
    address: str | None = None
    phone: str | None = None

    class Config:
        extra = "forbid"


class CustomerResponse(CustomerBase):
    customer_id: UUID = Field(alias="id")
    created_at: datetime

    class Config:
        from_attributes = True
