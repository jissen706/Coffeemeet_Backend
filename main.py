from fastapi import FastAPI
from database import engine, Base
import models
from routers import owners, baristas, customers, slots, cafes

Base.metadata.create_all(bind=engine)

app = FastAPI()

app.include_router(owners.router)
app.include_router(baristas.router)
app.include_router(customers.router)
app.include_router(cafes.router)
app.include_router(slots.router)