from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database import get_db
import models, schemas
from argon2 import PasswordHasher
ph = PasswordHasher()

router = APIRouter()

@router.get("/cafes/{cafe_id}", response_model=schemas.CafeResponse)
def get_cafe(cafe_id: int, db: Session = Depends(get_db)):
    cafe = db.query(models.Cafe).filter(models.Cafe.id == cafe_id).first()
    
    if not cafe:
        raise HTTPException(status_code=404, detail="Cafe not found")
    
    return cafe

@router.get("/cafes/{cafe_id}/slots", response_model=list[schemas.SlotResponse])
def get_slots(cafe_id: int, db: Session = Depends(get_db)):
    slots = db.query(models.Slot).filter(models.Slot.cafe_id == cafe_id).all()

    return slots

@router.post("/cafes", response_model=schemas.CafeResponse)
def create_cafe(cafe: schemas.CafeCreate, db: Session = Depends(get_db)):
    db_cafe = models.Cafe(
        name=cafe.name,
        start_date=cafe.start_date,
        end_date=cafe.end_date,
        owner_id=cafe.owner_id
    )
    db.add(db_cafe)
    db.commit()
    db.refresh(db_cafe)
    return db_cafe
