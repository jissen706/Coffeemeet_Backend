from datetime import datetime, date
from pydantic import BaseModel, field_validator, Field
from typing import Optional, Any, List


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
    description: Optional[str] = None
    max_participants: int = Field(default=1, ge=1, le=100)

class CafeUpdate(BaseModel):
    name: Optional[str] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    one_slot: Optional[bool] = None
    description: Optional[str] = None
    max_participants: Optional[int] = Field(default=None, ge=1, le=100)

class CafeResponse(BaseModel):
    id: int
    name: str
    start_date: date
    end_date: date
    one_slot: bool
    join_code: str
    participant_code: str
    owner_id: int
    description: Optional[str] = None
    max_participants: int = 1

    class Config:
        from_attributes = True


class PublicCafeResponse(BaseModel):
    """Returned on participant-facing public endpoints — join_code is omitted."""
    id: int
    name: str
    start_date: date
    end_date: date
    one_slot: bool
    participant_code: str
    description: Optional[str] = None
    max_participants: int = 1

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

class CustomerLookup(BaseModel):
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
    """Used in public slot endpoints — email omitted to protect customer privacy."""
    id: int
    name: str

    class Config:
        from_attributes = True


class SlotCustomerResponseFull(BaseModel):
    """Used in host-authenticated slot endpoints — includes email."""
    id: int
    name: str
    email: str

    class Config:
        from_attributes = True



def _validate_meet_link(v: Optional[str]) -> Optional[str]:
    if v is None:
        return v
    v = v.strip()
    if not v:
        return None
    if not (v.startswith("http://") or v.startswith("https://")):
        raise ValueError("Virtual meeting link must start with http:// or https://")
    return v


class SlotCreate(BaseModel):
    cafe_id: int
    start_time: datetime
    end_time: datetime
    location: str
    barista_id: int
    meet_link: Optional[str] = None
    notes: Optional[str] = None

    @field_validator("meet_link", mode="before")
    @classmethod
    def validate_meet_link(cls, v):
        return _validate_meet_link(v)

class SlotMeetLink(BaseModel):
    meet_link: str

    @field_validator("meet_link", mode="before")
    @classmethod
    def validate_meet_link(cls, v):
        return _validate_meet_link(v)

class SlotEdit(BaseModel):
    location: Optional[str] = None
    meet_link: Optional[str] = None
    notes: Optional[str] = None

    @field_validator("meet_link", mode="before")
    @classmethod
    def validate_meet_link(cls, v):
        return _validate_meet_link(v)

class SlotBook(BaseModel):
    customer_id: int

class SlotResponse(BaseModel):
    id: int
    cafe_id: int
    start_time: datetime
    end_time: datetime
    location: str
    meet_link: Optional[str] = None
    notes: Optional[str] = None
    status: str
    barista: BaristaResponse
    customers: List[SlotCustomerResponse] = []
    max_participants: int = 1
    spots_left: int = 0

    class Config:
        from_attributes = True


class SlotResponseFull(BaseModel):
    """Returned by host-authenticated endpoints — customer email included."""
    id: int
    cafe_id: int
    start_time: datetime
    end_time: datetime
    location: str
    meet_link: Optional[str] = None
    notes: Optional[str] = None
    status: str
    barista: BaristaResponse
    customers: List[SlotCustomerResponseFull] = []
    max_participants: int = 1
    spots_left: int = 0

    class Config:
        from_attributes = True
