import logging
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter
from fastapi import Depends
from fastapi import Header
from fastapi import HTTPException
from fastapi import status
from sqlalchemy.orm import Session

from db.helpers import get_all_admin_ids
from db.models import Customer
from db.session import get_db

logger = logging.getLogger(__name__)


admins_router = APIRouter()


@admins_router.put(
    "/{customer_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    responses={status.HTTP_403_FORBIDDEN: {}, status.HTTP_404_NOT_FOUND: {}},
)
def add_admin(
    customer_id: UUID,
    db: Annotated[Session, Depends(get_db)],
    x_is_admin: Annotated[bool | None, Header()] = None,
):
    if not x_is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="You don't have admin rights"
        )

    db_customer = db.get(Customer, customer_id)
    if not db_customer:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Customer not found"
        )

    db_customer.is_admin = True
    db.commit()


@admins_router.get(
    "/", response_model=list[UUID], responses={status.HTTP_403_FORBIDDEN: {}}
)
def get_admins(
    db: Annotated[Session, Depends(get_db)],
    x_is_admin: Annotated[bool | None, Header()] = None,
):
    if not x_is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="You don't have admin rights"
        )

    return get_all_admin_ids(db)


@admins_router.delete(
    "/{customer_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    responses={
        status.HTTP_400_BAD_REQUEST: {},
        status.HTTP_403_FORBIDDEN: {},
        status.HTTP_404_NOT_FOUND: {},
    },
)
def remove_admin(
    customer_id: UUID,
    db: Annotated[Session, Depends(get_db)],
    x_is_admin: Annotated[bool | None, Header()] = None,
):
    if not x_is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="You don't have admin rights"
        )

    db_customer = db.get(Customer, customer_id)
    if not db_customer:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Customer not found"
        )

    all_admin_ids = get_all_admin_ids(db)
    if len(all_admin_ids) <= 1 and db_customer.is_admin:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Can't remove admin, there is only 1 admin left",
        )

    db_customer.is_admin = False
    db.commit()
