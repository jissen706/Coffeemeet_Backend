from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError
from database import get_db
import models, schemas
from auth import create_token, get_current_user

router = APIRouter()
ph = PasswordHasher()


@router.post("/owners", response_model=schemas.TokenResponse)
def create_owner(owner: schemas.OwnerCreate, db: Session = Depends(get_db)):
    existing = db.query(models.Owner).filter(models.Owner.email == owner.email).first()
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")

    hashed = ph.hash(owner.password)
    db_owner = models.Owner(name=owner.name, email=owner.email, hashed_password=hashed)
    db.add(db_owner)
    db.commit()
    db.refresh(db_owner)

    token = create_token({"sub": str(db_owner.id), "role": "owner", "name": db_owner.name})
    return {
        "access_token": token,
        "token_type": "bearer",
        "user": {"id": db_owner.id, "name": db_owner.name, "role": "owner"},
    }


@router.post("/owners/login", response_model=schemas.TokenResponse)
def login_owner(body: schemas.OwnerLogin, db: Session = Depends(get_db)):
    owner = db.query(models.Owner).filter(models.Owner.email == body.email).first()

    if not owner:
        raise HTTPException(status_code=404, detail="Owner not found")

    try:
        ph.verify(owner.hashed_password, body.password)
    except VerifyMismatchError:
        raise HTTPException(status_code=401, detail="Incorrect password")

    token = create_token({"sub": str(owner.id), "role": "owner", "name": owner.name})
    return {
        "access_token": token,
        "token_type": "bearer",
        "user": {"id": owner.id, "name": owner.name, "role": "owner"},
    }


@router.get("/owners/{owner_id}/cafes", response_model=list[schemas.CafeResponse])
def get_owner_cafes(
    owner_id: int,
    user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if user.get("role") != "owner" or int(user["sub"]) != owner_id:
        raise HTTPException(status_code=403, detail="Not authorized")
    owner = db.query(models.Owner).filter(models.Owner.id == owner_id).first()
    if not owner:
        raise HTTPException(status_code=404, detail="Owner not found")
    return db.query(models.Cafe).filter(models.Cafe.owner_id == owner_id).all()
