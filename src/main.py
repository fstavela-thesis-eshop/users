import logging
from functools import partial

from fastapi import FastAPI

from api.admins import admins_router
from api.auth import auth_router
from api.customers import customers_router
from api.helpers import custom_openapi
from db.helpers import add_default_admin
from db.helpers import get_all_admin_ids
from db.session import get_db

logging.basicConfig(level=logging.INFO)

logger = logging.getLogger(__name__)

app = FastAPI()
app.include_router(customers_router, prefix="/customers", tags=["customers"])
app.include_router(auth_router, prefix="/auth", tags=["auth"])
app.include_router(admins_router, prefix="/admins", tags=["admins"])

app.openapi = partial(custom_openapi, app)  # type: ignore[method-assign]

if __name__ == "main":
    db = next(get_db())
    if len(get_all_admin_ids(db)) == 0:
        add_default_admin(db)
