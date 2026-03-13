from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database import get_db
import models, schemas

router = APIRouter()

@router.post("/customers/{cafe_id}", response_model=schemas.CustomerResponse)
def create_customer(cafe_id: int, customer: schemas.CustomerCreate, db: Session = Depends(get_db)):
    db_customer = models.Customer(name=customer.name, cafe_id=cafe_id)
    
    db.add(db_customer)
    db.commit()
    db.refresh(db_customer)
    
    return db_customer