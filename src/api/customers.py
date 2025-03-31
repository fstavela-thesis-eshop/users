import logging
from typing import Annotated
from uuid import UUID

import bcrypt
from fastapi import APIRouter
from fastapi import Depends
from fastapi import Header
from fastapi import HTTPException
from fastapi import status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from db.models import Customer
from db.session import get_db
from schemas.customer_schemas import CustomerCreate
from schemas.customer_schemas import CustomerResponse
from schemas.customer_schemas import CustomerUpdate

logger = logging.getLogger(__name__)


customers_router = APIRouter()


@customers_router.get("", response_model=list[CustomerResponse])
def get_customers(
    x_customer_id: Annotated[str, Header()],
    x_is_admin: Annotated[bool, Header()],
    db: Annotated[Session, Depends(get_db)],
) -> list[Customer]:
    if x_is_admin:
        return list(db.scalars(select(Customer)).all())
    return [db.get(Customer, x_customer_id)]


@customers_router.get(
    "/{customer_id}",
    response_model=CustomerResponse,
    responses={status.HTTP_403_FORBIDDEN: {}, status.HTTP_404_NOT_FOUND: {}},
)
def get_customer(
    customer_id: UUID,
    x_customer_id: Annotated[str, Header()],
    x_is_admin: Annotated[bool, Header()],
    db: Annotated[Session, Depends(get_db)],
) -> Customer:
    if str(customer_id) != x_customer_id and not x_is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can't get a different customer's data",
        )

    db_customer = db.get(Customer, customer_id)
    if not db_customer:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Customer not found"
        )

    return db_customer


@customers_router.post(
    "/create",
    response_model=CustomerResponse,
    status_code=status.HTTP_201_CREATED,
    responses={status.HTTP_400_BAD_REQUEST: {}},
)
def create_customer(
    input_customer: CustomerCreate, db: Annotated[Session, Depends(get_db)]
) -> Customer:
    hashed_password = bcrypt.hashpw(
        input_customer.password.encode("utf-8"), bcrypt.gensalt()
    )
    db_customer = Customer(
        username=input_customer.username,
        password=hashed_password.decode(),
        first_name=input_customer.first_name,
        last_name=input_customer.last_name,
        email=input_customer.email,
        address=input_customer.address,
        phone=input_customer.phone,
    )

    try:
        db.add(db_customer)
        db.commit()
    except IntegrityError as err:
        logger.error(f"Error while creating a new customer: {err.args}")
        err_message = err.args[0].split("\n")[-2]
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=err_message
        ) from err

    db.refresh(db_customer)
    return db_customer


@customers_router.patch(
    "/{customer_id}",
    response_model=CustomerResponse,
    responses={
        status.HTTP_400_BAD_REQUEST: {},
        status.HTTP_403_FORBIDDEN: {},
        status.HTTP_404_NOT_FOUND: {},
    },
)
def update_customer(
    customer_id: UUID,
    input_customer: CustomerUpdate,
    x_customer_id: Annotated[str, Header()],
    x_is_admin: Annotated[bool, Header()],
    db: Annotated[Session, Depends(get_db)],
) -> Customer:
    if str(customer_id) != x_customer_id and not x_is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can't update a different customer",
        )

    db_customer = db.get(Customer, customer_id)
    if not db_customer:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Customer not found"
        )

    update_data = input_customer.model_dump(exclude_unset=True)
    for k, v in update_data.items():
        setattr(db_customer, k, v)

    try:
        db.commit()
    except IntegrityError as err:
        logger.error(f"Error while updating a customer: {err.args}")
        err_message = err.args[0].split("\n")[-2]
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=err_message
        ) from err

    db.refresh(db_customer)
    return db_customer
