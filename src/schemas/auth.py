from uuid import UUID

from pydantic import BaseModel, Field


class AuthResponse(BaseModel):
    id: UUID
    is_admin: bool
