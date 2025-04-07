import logging
from typing import cast
from uuid import UUID

import bcrypt
from sqlalchemy import select
from sqlalchemy.orm import Session

from db.models import Customer

logger = logging.getLogger(__name__)


def get_all_admin_ids(db: Session) -> list[UUID]:
    query = select(Customer.id).where(Customer.is_admin)
    return cast(list[UUID], db.scalars(query).all())


def add_default_admin(db: Session) -> None:
    logger.info("Adding default admin")
    hashed_password = bcrypt.hashpw(b"admin", bcrypt.gensalt())
    db.add(
        Customer(
            username="admin",
            password=hashed_password.decode("utf-8"),
            first_name="admin",
            last_name="admin",
            email="admin@example.com",
            address="admin",
            phone="+420 123 456 789",
            is_admin=True,
        )
    )
    db.commit()
