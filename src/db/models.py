from uuid import uuid4
from datetime import datetime, timezone
from sqlalchemy import Column, String, UUID, DateTime, Boolean
from sqlalchemy.orm import declarative_base


Base = declarative_base()

def _time_now():
    return datetime.now(timezone.utc)


class Customer(Base):
    __tablename__ = "customers"

    id = Column(UUID(as_uuid=True), nullable=False, unique=True, primary_key=True, default=uuid4)
    username = Column(String(255), nullable=False, unique=True)
    password = Column(String(255), nullable=False)
    first_name = Column(String(32), nullable=False)
    last_name = Column(String(32), nullable=False)
    email = Column(String(128), nullable=False, unique=True)
    address = Column(String(256), nullable=False)
    phone = Column(String(20), nullable=False)
    created_at = Column(DateTime(timezone=True), nullable=False, default=_time_now)
