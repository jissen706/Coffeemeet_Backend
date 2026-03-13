from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError
from database import get_db
import models, schemas

router = APIRouter()
ph = PasswordHasher()

@router.post("/owners", response_model=schemas.OwnerResponse)
def create_owner(owner: schemas.OwnerCreate, db: Session = Depends(get_db)):
    hashed = ph.hash(owner.password)
    db_owner = models.Owner(name=owner.name, email=owner.email, password=hashed)
    db.add(db_owner)
    db.commit()
    db.refresh(db_owner)
    return db_owner

@router.post("/owners/login")
def login_owner(email: str, password: str, db: Session = Depends(get_db)):
    owner = db.query(models.Owner).filter(models.Owner.email == email).first()
    
    if not owner:
        raise HTTPException(status_code=404, detail="Owner not found")
    
    try:
        ph.verify(owner.password, password)
    except VerifyMismatchError:
        raise HTTPException(status_code=400, detail="Incorrect password")
    
    return {"owner_id": owner.id, "name": owner.name}