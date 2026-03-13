from datetime import datetime, date
from pydantic import BaseModel
from typing import Optional


class OwnerCreate(BaseModel):
    name: str
    email: str
    password: str

class OwnerResponse(BaseModel):
    id: int
    name: str
    email: str

    class Config:
        from_attributes = True

class CustomerCreate(BaseModel):
    name: str

class CustomerResponse(BaseModel):
    id: int
    name: str

    class Config:
        from_attributes = True

class BaristaCreate(BaseModel):
    name: str
    email: str
    phone_number: Optional[str] = None
    join_code: str

class BaristaResponse(BaseModel):
    id: int
    name: str
    email: str
    phone_number: Optional[str] = None

    class Config:
        from_attributes = True

class SlotCreate(BaseModel):
    cafe_id: int
    start_time: datetime
    end_time: datetime
    location: str
    barista_id: int
    meet_link: Optional[str] = None

class SlotMeetLink(BaseModel):
    meet_link: str

class SlotResponse(BaseModel):
    cafe_id: int
    id: int
    start_time: datetime
    end_time: datetime
    location: str
    meet_link: Optional[str] = None
    barista: BaristaResponse
    customer: Optional[CustomerResponse] = None
    class Config:
        from_attributes = True

class CafeCreate(BaseModel):
    name: str
    owner_id: int
    start_date: date
    end_date: date

class CafeResponse(BaseModel):
    id: int
    name: str
    start_date: date
    end_date: date
    join_code: str

class SlotBook(BaseModel):
    customer_id: int
