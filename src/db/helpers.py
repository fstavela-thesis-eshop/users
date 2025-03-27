from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from db.models import Customer


def get_all_admin_ids(db: Session) -> list[UUID]:
    stmt = select(Customer.id).where(Customer.is_admin)
    return list(db.execute(stmt).scalars().all())
