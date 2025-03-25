import bcrypt
from fastapi import APIRouter, Depends, Header, HTTPException, status, Response
from db.session import get_db
from sqlalchemy.orm import Session
from schemas.customers import CustomerResponse, CustomerCreate, CustomerUpdate
from db.models import Customer
import logging
from uuid import UUID
from sqlalchemy.exc import IntegrityError

logger = logging.getLogger(__name__)


customers_router = APIRouter()


@customers_router.post("/", response_model=CustomerResponse, status_code=status.HTTP_201_CREATED, responses={status.HTTP_400_BAD_REQUEST: {}})
def create_customer(customer: CustomerCreate, db: Session = Depends(get_db)):
    hashed_password = bcrypt.hashpw(customer.password.encode("utf-8"), bcrypt.gensalt())
    db_customer = Customer(
        username=customer.username,
        password=hashed_password.decode(),
        first_name=customer.first_name,
        last_name=customer.last_name,
        email=customer.email,
        address=customer.address,
        phone=customer.phone,
    )

    try:
        db.add(db_customer)
        db.commit()
    except IntegrityError as err:
        logger.error(f"Error while creating a new customer: {err.args}")
        err_message = err.args[0].split("\n")[-2]
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=err_message)

    db.refresh(db_customer)
    return db_customer


@customers_router.get("/", response_model=list[CustomerResponse])
def get_customers(x_customer_id: str = Header(), db: Session = Depends(get_db)):
    return [db.get(Customer, x_customer_id)]


@customers_router.patch("/{customer_id}", response_model=CustomerResponse, responses={status.HTTP_400_BAD_REQUEST: {}, status.HTTP_401_UNAUTHORIZED: {}})
def update_customer(customer_id: UUID, customer: CustomerUpdate, x_customer_id: str = Header(), db: Session = Depends(get_db)):
    if str(customer_id) != x_customer_id:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="You can't update a different customer")

    db_customer = db.get(Customer, customer_id)

    update_data = customer.model_dump(exclude_unset=True)
    for k, v in update_data.items():
        setattr(db_customer, k, v)

    try:
        db.commit()
    except IntegrityError as err:
        logger.error(f"Error while creating a new customer: {err.args}")
        err_message = err.args[0].split("\n")[-2]
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=err_message)

    db.refresh(db_customer)
    return db_customer
