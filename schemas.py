from datetime import datetime, date
from pydantic import BaseModel
from typing import Optional, Any


# ── Owner ──────────────────────────────────────────────────────────────────────

class OwnerCreate(BaseModel):
    name: str
    email: str
    password: str

class OwnerLogin(BaseModel):
    email: str
    password: str

class OwnerResponse(BaseModel):
    id: int
    name: str
    email: str

    class Config:
        from_attributes = True


# ── Token ──────────────────────────────────────────────────────────────────────

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: dict[str, Any]


# ── Cafe ───────────────────────────────────────────────────────────────────────

class CafeCreate(BaseModel):
    name: str
    start_date: date
    end_date: date
    one_slot: bool

class CafeUpdate(BaseModel):
    name: Optional[str] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    one_slot: Optional[bool] = None

class CafeResponse(BaseModel):
    id: int
    name: str
    start_date: date
    end_date: date
    one_slot: bool
    join_code: str
    participant_code: str
    owner_id: int

    class Config:
        from_attributes = True


# ── Barista ────────────────────────────────────────────────────────────────────

class BaristaCreate(BaseModel):
    name: str
    email: str
    phone_number: Optional[str] = None
    bio: Optional[str] = None
    join_code: str

class BaristaResponse(BaseModel):
    id: int
    name: str
    email: str
    phone_number: Optional[str] = None
    bio: Optional[str] = None
    cafe_id: int

    class Config:
        from_attributes = True


# ── Customer ───────────────────────────────────────────────────────────────────

class CustomerCreate(BaseModel):
    name: str
    email: str

class CustomerResponse(BaseModel):
    id: int
    name: str
    email: str
    cafe_id: int

    class Config:
        from_attributes = True


# ── Slot ───────────────────────────────────────────────────────────────────────

class SlotCustomerResponse(BaseModel):
    id: int
    name: str
    email: str

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

class SlotEdit(BaseModel):
    location: Optional[str] = None
    meet_link: Optional[str] = None

class SlotBook(BaseModel):
    customer_id: int

class SlotResponse(BaseModel):
    id: int
    cafe_id: int
    start_time: datetime
    end_time: datetime
    location: str
    meet_link: Optional[str] = None
    status: str
    barista: BaristaResponse
    customer: Optional[SlotCustomerResponse] = None

    class Config:
        from_attributes = True
