from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field

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


class CustomerUpdate(CustomerBase):
    pass


class CustomerResponse(CustomerBase):
    customer_id: UUID = Field(alias="id")
    created_at: datetime

    class Config:
        from_attributes = True
