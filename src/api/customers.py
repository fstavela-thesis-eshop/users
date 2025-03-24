import bcrypt
from fastapi import APIRouter, Depends, Header, HTTPException, status
from db.session import get_db
from sqlalchemy.orm import Session
from schemas.customers import CustomerResponse, CustomerCreate
from db.models import Customer
from sqlalchemy import select
import logging

logger = logging.getLogger(__name__)


customers_router = APIRouter()


@customers_router.post("/", response_model=CustomerResponse)
def create_customer(customer: CustomerCreate, db: Session = Depends(get_db)):
    logger.warning(customer)
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
    db.add(db_customer)
    db.commit()
    db.refresh(db_customer)
    return db_customer


@customers_router.get("/", response_model=list[CustomerResponse])
def get_customers(x_customer_id: str = Header(None), db: Session = Depends(get_db)):
    logger.warning(f"Header: {x_customer_id}, type: {type(x_customer_id)} hahhaha")
    if not x_customer_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Missing authentication")

    stmt = select(Customer).where(Customer.id == x_customer_id)
    customers = db.execute(stmt).scalars().all()
    return customers
