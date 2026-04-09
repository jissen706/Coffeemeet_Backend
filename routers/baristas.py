from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database import get_db
import models, schemas
from auth import create_token, require_owner

router = APIRouter()


@router.post("/baristas", response_model=schemas.TokenResponse)
def register_or_login_barista(barista: schemas.BaristaCreate, db: Session = Depends(get_db)):
    cafe = db.query(models.Cafe).filter(models.Cafe.join_code == barista.join_code).first()
    if not cafe:
        raise HTTPException(status_code=404, detail="Cafe not found — check your join code")

    # If this email already belongs to a barista in this cafe, treat as login
    existing = db.query(models.Barista).filter(
        models.Barista.email == barista.email,
        models.Barista.cafe_id == cafe.id,
    ).first()

    if existing:
        db_barista = existing
    elif barista.name == '_return_':
        raise HTTPException(status_code=404, detail="No host account found for that email in this café")
    else:
        db_barista = models.Barista(
            name=barista.name,
            email=barista.email,
            phone_number=barista.phone_number,
            bio=barista.bio,
            cafe_id=cafe.id,
        )
        db.add(db_barista)
        db.commit()
        db.refresh(db_barista)

    token = create_token({
        "sub": str(db_barista.id),
        "role": "barista",
        "name": db_barista.name,
        "cafe_id": db_barista.cafe_id,
    })
    return {
        "access_token": token,
        "token_type": "bearer",
        "user": {
            "id": db_barista.id,
            "name": db_barista.name,
            "role": "barista",
            "cafe_id": db_barista.cafe_id,
        },
    }


@router.delete("/baristas/{barista_id}", status_code=204)
def remove_barista(
    barista_id: int,
    owner: dict = Depends(require_owner),
    db: Session = Depends(get_db),
):
    barista = db.query(models.Barista).filter(models.Barista.id == barista_id).first()
    if not barista:
        raise HTTPException(status_code=404, detail="Barista not found")

    cafe = db.query(models.Cafe).filter(
        models.Cafe.id == barista.cafe_id,
        models.Cafe.owner_id == int(owner["sub"]),
    ).first()
    if not cafe:
        raise HTTPException(status_code=403, detail="Not authorized to modify this cafe")

    # Cascade: delete all slots created by this barista
    db.query(models.Slot).filter(models.Slot.barista_id == barista_id).delete()
    db.delete(barista)
    db.commit()
