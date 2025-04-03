import logging

from fastapi import FastAPI

from api.admins import admins_router
from api.auth import auth_router
from api.customers import customers_router
from db.helpers import add_default_admin
from db.helpers import get_all_admin_ids
from db.session import get_db

logging.basicConfig(level=logging.INFO)

app = FastAPI()
app.include_router(customers_router, prefix="/customers", tags=["customers"])
app.include_router(auth_router, prefix="/auth", tags=["auth"])
app.include_router(admins_router, prefix="/admins", tags=["admins"])


db = next(get_db())
if len(get_all_admin_ids(db)) == 0:
    add_default_admin(db)
