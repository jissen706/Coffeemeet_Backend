from sqlalchemy import Column, Integer, String, Date, DateTime, ForeignKey, Boolean, UniqueConstraint, func
from sqlalchemy.orm import relationship
from database import Base

import secrets
import string

def generate_cafe_code():
    # This creates a 6-character code like 'A8B2X9'
    characters = string.ascii_uppercase + string.digits
    return ''.join(secrets.choice(characters) for _ in range(6))

class Cafe(Base):
    __tablename__ = "cafes"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    start_date = Column(Date)
    end_date = Column(Date)
    join_code = Column(String, unique=True, default=generate_cafe_code)          # host-only
    participant_code = Column(String, unique=True, default=generate_cafe_code)  # participant-only
    one_slot = Column(Boolean, default=True)
    description = Column(String, nullable=True)
    # Group coffee chats: how many customers can book the same slot.
    # 1 = traditional 1:1; >1 = group chat that stays open until full.
    max_participants = Column(Integer, nullable=False, default=1, server_default="1")

    owner_id = Column(Integer, ForeignKey("owners.id"))
    owner = relationship("Owner", back_populates="cafes")
    baristas = relationship("Barista", back_populates="cafe", cascade="all, delete-orphan")
    customers = relationship("Customer", back_populates="cafe", cascade="all, delete-orphan")
    slots = relationship("Slot", back_populates="cafe", cascade="all, delete-orphan")

class Slot(Base):
    __tablename__ = "slots"
    id = Column(Integer, primary_key=True, index=True)
    start_time = Column(DateTime)
    end_time = Column(DateTime)
    location = Column(String, nullable=True)
    meet_link = Column(String, nullable=True)
    notes = Column(String, nullable=True)
    status = Column(String, default="open")

    cafe_id = Column(Integer, ForeignKey("cafes.id"))
    barista_id = Column(Integer, ForeignKey("baristas.id"))

    cafe = relationship("Cafe", back_populates="slots")
    barista = relationship("Barista", back_populates="slots")
    bookings = relationship(
        "SlotBooking",
        back_populates="slot",
        cascade="all, delete-orphan",
        order_by="SlotBooking.created_at",
    )

    @property
    def customers(self):
        return [b.customer for b in self.bookings if b.customer is not None]

    @property
    def max_participants(self):
        return self.cafe.max_participants if self.cafe else 1

    @property
    def spots_left(self):
        cap = self.cafe.max_participants if self.cafe else 1
        return max(0, cap - len(self.bookings))


class SlotBooking(Base):
    __tablename__ = "slot_bookings"
    id = Column(Integer, primary_key=True, index=True)
    slot_id = Column(Integer, ForeignKey("slots.id", ondelete="CASCADE"), nullable=False, index=True)
    customer_id = Column(Integer, ForeignKey("customers.id", ondelete="CASCADE"), nullable=False, index=True)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)

    slot = relationship("Slot", back_populates="bookings")
    customer = relationship("Customer", back_populates="bookings")

    __table_args__ = (UniqueConstraint("slot_id", "customer_id", name="uq_slot_booking"),)


class Owner(Base):
    __tablename__ = "owners"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)

    cafes = relationship("Cafe", back_populates="owner")

class Barista(Base):
    __tablename__ = "baristas"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    email = Column(String, nullable=False)
    phone_number = Column(String(20), nullable=True)
    bio = Column(String, nullable=True)

    cafe_id = Column(Integer, ForeignKey("cafes.id"))
    cafe = relationship("Cafe", back_populates="baristas")
    slots = relationship("Slot", back_populates="barista", cascade="all, delete-orphan")

    __table_args__ = (UniqueConstraint("email", "cafe_id", name="uq_barista_email_cafe"),)

class Customer(Base):
    __tablename__ = "customers"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    email = Column(String, nullable=False)
    cafe_id = Column(Integer, ForeignKey("cafes.id"))
    cafe = relationship("Cafe", back_populates="customers")
    bookings = relationship(
        "SlotBooking",
        back_populates="customer",
        cascade="all, delete-orphan",
    )

    __table_args__ = (UniqueConstraint("email", "cafe_id", name="uq_customer_email_cafe"),)
