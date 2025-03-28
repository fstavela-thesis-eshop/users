import logging
from typing import Annotated

import bcrypt
from fastapi import APIRouter
from fastapi import Depends
from fastapi import HTTPException
from fastapi import Response
from fastapi import status
from fastapi.security import HTTPBasic
from fastapi.security import HTTPBasicCredentials
from sqlalchemy import select
from sqlalchemy.orm import Session

from db.models import Customer
from db.session import get_db
from schemas.auth_schemas import AuthResponse

logger = logging.getLogger(__name__)


auth_router = APIRouter()
security = HTTPBasic()


@auth_router.get(
    "",
    response_model=AuthResponse,
    responses={status.HTTP_401_UNAUTHORIZED: {}},
)
def validate(
    response: Response,
    credentials: Annotated[HTTPBasicCredentials, Depends(security)],
    db: Annotated[Session, Depends(get_db)],
) -> Customer:
    stmt = select(Customer).where(Customer.username == credentials.username)
    customer = db.execute(stmt).scalar()
    if not customer or not bcrypt.checkpw(
        credentials.password.encode("utf-8"), customer.password.encode("utf-8")
    ):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials"
        )

    response.headers["x-customer-id"] = str(customer.id)
    response.headers["x-is-admin"] = str(customer.is_admin)
    return customer
