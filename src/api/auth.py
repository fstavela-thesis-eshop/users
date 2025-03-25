import bcrypt
from fastapi import APIRouter, Depends, HTTPException, status, Response
from fastapi.responses import JSONResponse
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from db.session import get_db
from sqlalchemy.orm import Session
from db.models import Customer
from sqlalchemy import select
import logging

from schemas.customers import AuthResponse

logger = logging.getLogger(__name__)


auth_router = APIRouter()
security = HTTPBasic()

@auth_router.get("/validate", response_model=AuthResponse, responses={status.HTTP_401_UNAUTHORIZED: {}})
def validate(response: Response, credentials: HTTPBasicCredentials = Depends(security), db: Session = Depends(get_db)):
    stmt = select(Customer).where(Customer.username == credentials.username)
    customer = db.execute(stmt).scalar()
    if not customer or not bcrypt.checkpw(credentials.password.encode("utf-8"), customer.password.encode("utf-8")):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")

    response.headers["x-customer-id"] = str(customer.id)
    return customer
