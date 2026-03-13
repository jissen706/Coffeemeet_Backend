from sqlalchemy import Column, Integer, String, Date, DateTime, ForeignKey, Boolean
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
    join_code = Column(String, unique = True, default=generate_cafe_code)

    owner_id = Column(Integer, ForeignKey("owners.id"))
    owner = relationship("Owner", back_populates="cafes")
    baristas = relationship("Barista", back_populates="cafe")
    customers = relationship("Customer", back_populates="cafe")
    slots = relationship("Slot", back_populates="cafe")

class Slot(Base):
    __tablename__ = "slots"
    id = Column(Integer, primary_key=True, index=True)
    start_time = Column(DateTime)
    end_time = Column(DateTime)
    location = Column(String, nullable=True)
    meet_link = Column(String, nullable=True)
    status = Column(String, default="open") 

    cafe_id = Column(Integer, ForeignKey("cafes.id"))
    barista_id = Column(Integer, ForeignKey("baristas.id"))
    customer_id = Column(Integer, ForeignKey("customers.id"), nullable=True)  # null = open slot

    cafe = relationship("Cafe", back_populates="slots")
    barista = relationship("Barista", back_populates="slots")
    customer = relationship("Customer", back_populates="slot") 


class Owner(Base):
    __tablename__ = "owners"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    password = Column(String, nullable=False)  # you'll hash this later

    cafes = relationship("Cafe", back_populates="owner")

class Barista(Base):
    __tablename__ = "baristas"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    phone_number = Column(String(20), nullable=True)
    
    cafe_id = Column(Integer, ForeignKey("cafes.id"))
    cafe = relationship("Cafe", back_populates="baristas")
    slots = relationship("Slot", back_populates="barista")

class Customer(Base):
    __tablename__ = "customers"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    cafe_id = Column(Integer, ForeignKey("cafes.id"))
    cafe = relationship("Cafe", back_populates="customers")
    slot = relationship("Slot", back_populates="customer", uselist=False)