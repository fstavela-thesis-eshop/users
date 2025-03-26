from fastapi import FastAPI
from api.customers import customers_router
from api.auth import auth_router
from api.admins import admins_router


app = FastAPI()
app.include_router(customers_router, prefix="/customers", tags=["customers"])
app.include_router(auth_router, prefix="/auth", tags=["auth"])
app.include_router(admins_router, prefix="/admins", tags=["admins"])