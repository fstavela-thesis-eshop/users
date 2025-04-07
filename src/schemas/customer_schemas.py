from datetime import datetime
from uuid import UUID

from pydantic import BaseModel
from pydantic import ConfigDict
from pydantic import EmailStr


class CustomerBase(BaseModel):
    username: str
    first_name: str
    last_name: str
    email: EmailStr
    address: str
    phone: str

    model_config = ConfigDict(extra="forbid")


class CustomerCreate(CustomerBase):
    password: str


class CustomerUpdate(BaseModel):
    password: str | None = None
    first_name: str | None = None
    last_name: str | None = None
    email: EmailStr | None = None
    address: str | None = None
    phone: str | None = None

    model_config = ConfigDict(extra="forbid")


class CustomerResponse(CustomerBase):
    id: UUID
    created_at: datetime
