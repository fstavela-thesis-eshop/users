from uuid import UUID

from pydantic import BaseModel


class AuthResponse(BaseModel):
    id: UUID
    is_admin: bool
