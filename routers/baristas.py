from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database import get_db
import models, schemas

router = APIRouter()


@router.post("/baristas", response_model=schemas.BaristaResponse)
def create_barista(barista: schemas.BaristaCreate, db: Session = Depends(get_db)):
    # 1. find the cafe by join code
    cafe = db.query(models.Cafe).filter(models.Cafe.join_code == barista.join_code).first()
    
    # 2. if not found, stop here
    if not cafe:
        raise HTTPException(status_code=404, detail="Cafe not found")
    
    # 3. create and save the barista, attaching them to the cafe
    db_barista = models.Barista(
        name=barista.name,
        email=barista.email,
        phone_number=barista.phone_number,
        cafe_id=cafe.id 
    )
    db.add(db_barista)
    db.commit()
    db.refresh(db_barista)
    
    return db_barista