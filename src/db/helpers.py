from sqlalchemy.orm import Session
from sqlalchemy import select
from uuid import UUID

from db.models import Customer


def get_db_customer_by_id(db: Session, customer_id: str | UUID) -> Customer | None:
    stmt = select(Customer).where(Customer.id == customer_id)
    return db.execute(stmt).scalar()
