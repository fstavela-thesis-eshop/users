from datetime import UTC
from datetime import datetime
from uuid import uuid4

from sqlalchemy import UUID
from sqlalchemy import Boolean
from sqlalchemy import Column
from sqlalchemy import DateTime
from sqlalchemy import String
from sqlalchemy.orm import declarative_base

Base = declarative_base()


def _time_now():
    return datetime.now(UTC)


class Customer(Base):  # type: ignore[valid-type, misc]
    __tablename__ = "customers"

    id = Column(
        UUID(as_uuid=True), nullable=False, unique=True, primary_key=True, default=uuid4
    )
    username = Column(String(255), nullable=False, unique=True, index=True)
    password = Column(String(255), nullable=False)
    first_name = Column(String(32), nullable=False)
    last_name = Column(String(32), nullable=False)
    email = Column(String(128), nullable=False, unique=True)
    address = Column(String(256), nullable=False)
    phone = Column(String(20), nullable=False)
    created_at = Column(DateTime(timezone=True), nullable=False, default=_time_now)
    is_admin = Column(Boolean, nullable=False, default=False)
